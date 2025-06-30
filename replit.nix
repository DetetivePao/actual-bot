{ pkgs }: {
  deps = [
    pkgs.python310
    pkgs.python310Packages.pip
    pkgs.ffmpeg
  ];

  env = {
    PIP_DISABLE_PIP_VERSION_CHECK = "1";
    PIP_NO_CACHE_DIR = "off";
  };

  postInstall = ''
    pip install flask
    pip install discord.py
    pip install yt-dlp
    pip install pyttsx3
    pip install language-tool-python
  '';
}
