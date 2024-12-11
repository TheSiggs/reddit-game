{ pkgs ? import <nixpkgs> { } }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python312
    zsh
    poetry
    glib
    SDL2
    SDL2_mixer
    obs-studio
  ];

  allowUnfree = true;

  shellHook = ''
    # Ensure Poetry uses virtual environments in the project directory
    poetry config virtualenvs.in-project true --local

    # Reinstall dependencies if needed
    poetry install

    # Activate the Poetry-managed virtual environment
    if [ -f .venv/bin/activate ]; then
      source .venv/bin/activate
    else
      echo "Virtual environment not found. Run 'poetry install' to create it."
    fi

    # Launch Zsh
    exec zsh
  '';
}

