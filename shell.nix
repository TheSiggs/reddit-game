{ pkgs ? import <nixpkgs> { } }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    (python312.withPackages (ps: [ ps.pygame ps.librosa ps.numpy ps.google-cloud-texttospeech ps.python-dotenv]))
    glib
    SDL2
    SDL2_mixer
    obs-studio
  ];

  shellHook = ''
    echo "Python environment with pygame set up."
    exec zsh
  '';
}

