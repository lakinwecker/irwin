{ pkgs, inputs, lib, config, ... }:
let
  python = pkgs.python311;

  n2c = inputs.nix2container.packages.${pkgs.system}.nix2container;
  skopeo-nix2container =
    inputs.nix2container.packages.${pkgs.system}.skopeo-nix2container;

  # uv2nix setup - similar to rustPlatform.buildRustPackage but for Python/uv
  workspace = inputs.uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };

  overlay = workspace.mkPyprojectOverlay {
    sourcePreference = "wheel";
  };

  pyprojectOverrides = final: prev: {
    # python-chess needs setuptools as build dependency
    python-chess = prev.python-chess.overrideAttrs (old: {
      nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ [
        final.setuptools
      ];
    });

    # tensorflow-io-gcs-filesystem needs tensorflow's native lib
    tensorflow-io-gcs-filesystem = prev.tensorflow-io-gcs-filesystem.overrideAttrs (old: {
      autoPatchelfIgnoreMissingDeps = [ "libtensorflow_framework.so.2" ];
    });
  };

  pythonSet =
    (pkgs.callPackage inputs.pyproject-nix.build.packages {
      inherit python;
    }).overrideScope
      (lib.composeManyExtensions [
        inputs.pyproject-build-systems.overlays.default
        overlay
        pyprojectOverrides
      ]);

  # Build the virtual environment with all dependencies
  irwinVenv = pythonSet.mkVirtualEnv "irwin-env" workspace.deps.default;

  # Source files
  irwinSrc = pkgs.stdenv.mkDerivation {
    name = "irwin-src";
    src = lib.cleanSource ./.;
    phases = [ "installPhase" ];
    installPhase = ''
      mkdir -p $out
      cp -r $src/* $out/
    '';
  };

  # Stockfish binary for deep-queue container
  stockfishBin = pkgs.stdenv.mkDerivation {
    name = "stockfish-bin";
    src = ./stockfish;
    nativeBuildInputs = [ pkgs.autoPatchelfHook ];
    buildInputs = [ pkgs.stdenv.cc.cc.lib ];
    phases = [ "installPhase" "fixupPhase" ];
    installPhase = ''
      mkdir -p $out/bin
      cp $src/stockfish-x86_64-modern $out/bin/stockfish
      chmod +x $out/bin/stockfish
    '';
  };

  # Container with Python and pre-installed dependencies
  makeContainer = { name, entrypoint, extraPackages ? [], extraEnv ? [] }:
    n2c.buildImage {
      name = name;
      tag = "latest";
      copyToRoot = pkgs.buildEnv {
        name = "root";
        paths = [
          pkgs.cacert
          pkgs.bashInteractive
          pkgs.coreutils
          pkgs.zlib
          pkgs.stdenv.cc.cc.lib
          irwinVenv
          irwinSrc
        ] ++ extraPackages;
        pathsToLink = [ "/bin" "/lib" "/etc" ];
      };
      config = {
        WorkingDir = "/app";
        Env = [
          "SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
          "PATH=/bin:${irwinVenv}/bin"
          "PYTHONPATH=${irwinSrc}"
          "HOME=/tmp"
          "TF_USE_LEGACY_KERAS=1"
          "LD_LIBRARY_PATH=${pkgs.zlib}/lib:${pkgs.stdenv.cc.cc.lib}/lib"
        ] ++ extraEnv;
        Entrypoint = [
          "${irwinVenv}/bin/python"
          "${irwinSrc}/${entrypoint}"
        ];
      };
    };

  lichessListenerContainer = makeContainer {
    name = "irwin-lichess-listener";
    entrypoint = "lichess-listener.py";
    extraEnv = [
      "IRWIN_MODEL_BASIC_FILE=/etc/irwin/models/basicGame.h5"
      "IRWIN_MODEL_ANALYSED_FILE=/etc/irwin/models/analysedGame.h5"
    ];
  };

  irwinWebappContainer = makeContainer {
    name = "irwin-webapp";
    entrypoint = "app.py";
    extraEnv = [
      "IRWIN_MODEL_BASIC_FILE=/etc/irwin/models/basicGame.h5"
      "IRWIN_MODEL_ANALYSED_FILE=/etc/irwin/models/analysedGame.h5"
    ];
  };

  deepQueueContainer = makeContainer {
    name = "irwin-deep-queue";
    entrypoint = "client.py";
    extraPackages = [ stockfishBin ];
    extraEnv = [ "IRWIN_STOCKFISH_PATH=/bin/stockfish" ];
  };

in {
  packages = [ pkgs.stockfish pkgs.zlib pkgs.stdenv.cc.cc.lib ];

  env.LD_LIBRARY_PATH = lib.makeLibraryPath [ pkgs.zlib pkgs.stdenv.cc.cc.lib ];

  env.TF_USE_LEGACY_KERAS = "1";

  languages.python = {
    enable = true;
    package = python;
    uv = {
      enable = true;
      sync.enable = true;
    };
  };

  services.mongodb.enable = true;

  processes = {
    lichess-listener.exec = "uv run python lichess-listener.py";
    webapp.exec = "uv run python app.py";
    deep-queue.exec = "uv run python client.py";
  };

  scripts.dev-listener.exec = "uv run python lichess-listener.py";
  scripts.dev-webapp.exec = "uv run python app.py";
  scripts.dev-deep-queue.exec = "uv run python client.py";

  scripts.container-load-listener.exec = ''
    ${skopeo-nix2container}/bin/skopeo --insecure-policy copy nix:${lichessListenerContainer} docker-daemon:irwin-lichess-listener:latest
  '';

  scripts.container-load-webapp.exec = ''
    ${skopeo-nix2container}/bin/skopeo --insecure-policy copy nix:${irwinWebappContainer} docker-daemon:irwin-webapp:latest
  '';

  scripts.container-load-deep-queue.exec = ''
    ${skopeo-nix2container}/bin/skopeo --insecure-policy copy nix:${deepQueueContainer} docker-daemon:irwin-deep-queue:latest
  '';

  scripts.container-load-all.exec = ''
    echo "Loading lichess-listener..."
    ${skopeo-nix2container}/bin/skopeo --insecure-policy copy nix:${lichessListenerContainer} docker-daemon:irwin-lichess-listener:latest
    echo "Loading webapp..."
    ${skopeo-nix2container}/bin/skopeo --insecure-policy copy nix:${irwinWebappContainer} docker-daemon:irwin-webapp:latest
    echo "Loading deep-queue..."
    ${skopeo-nix2container}/bin/skopeo --insecure-policy copy nix:${deepQueueContainer} docker-daemon:irwin-deep-queue:latest
    echo "Done."
  '';

  scripts.container-push-listener.exec = ''
    dest="$1"
    shift
    ${skopeo-nix2container}/bin/skopeo --insecure-policy copy "$@" nix:${lichessListenerContainer} "$dest"
  '';

  scripts.container-push-webapp.exec = ''
    dest="$1"
    shift
    ${skopeo-nix2container}/bin/skopeo --insecure-policy copy "$@" nix:${irwinWebappContainer} "$dest"
  '';

  scripts.container-push-deep-queue.exec = ''
    dest="$1"
    shift
    ${skopeo-nix2container}/bin/skopeo --insecure-policy copy "$@" nix:${deepQueueContainer} "$dest"
  '';
}
