{ pkgs, inputs, lib, config, ... }:
let
  python = pkgs.python311;

  n2c = inputs.nix2container.packages.${pkgs.system}.nix2container;
  skopeo-nix2container = inputs.nix2container.packages.${pkgs.system}.skopeo-nix2container;

  irwinSrc = pkgs.stdenv.mkDerivation {
    name = "irwin-src";
    src = lib.cleanSource ./.;
    phases = [ "installPhase" ];
    installPhase = ''
      mkdir -p $out
      cp -r $src/* $out/
    '';
  };

  # Container with Python, uv, and dependencies pre-installed
  makeContainer = { name, entrypoint }: n2c.buildImage {
    name = name;
    tag = "latest";
    copyToRoot = pkgs.buildEnv {
      name = "root";
      paths = [
        python
        pkgs.uv
        pkgs.cacert
        pkgs.stockfish
        pkgs.bashInteractive
        pkgs.coreutils
        irwinSrc
      ];
      pathsToLink = [ "/bin" "/lib" "/etc" ];
    };
    config = {
      WorkingDir = "${irwinSrc}";
      Env = [
        "SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
        "PATH=/bin"
        "PYTHONPATH=${irwinSrc}"
        "HOME=/tmp"
        "UV_CACHE_DIR=/tmp/.uv-cache"
        "TF_USE_LEGACY_KERAS=1"
      ];
      Entrypoint = [
        "${pkgs.bashInteractive}/bin/bash" "-c"
        "cd ${irwinSrc} && uv sync && uv run python ${entrypoint}"
      ];
    };
  };

  lichessListenerContainer = makeContainer {
    name = "irwin-lichess-listener";
    entrypoint = "lichess-listener.py";
  };

  irwinWebappContainer = makeContainer {
    name = "irwin-webapp";
    entrypoint = "app.py";
  };

  deepQueueContainer = makeContainer {
    name = "irwin-deep-queue";
    entrypoint = "client.py";
  };

in {
  packages = [
    pkgs.stockfish
    pkgs.zlib
    pkgs.stdenv.cc.cc.lib
  ];

  env.LD_LIBRARY_PATH = lib.makeLibraryPath [
    pkgs.zlib
    pkgs.stdenv.cc.cc.lib
  ];

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
