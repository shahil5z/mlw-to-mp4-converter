<div align="center">

# MLW to MP4 Converter

**A Windows tool for converting MyLiveWallpapers `.mlw` video wallpapers into standard `.mp4` files.**

Convert downloaded MLW wallpapers when you need a video file that can be opened, played, edited, or managed with regular Windows media software.

</div>

---

## Why use this?

MyLiveWallpapers video downloads use the `.mlw` format. This tool extracts the video into a standard MP4 file, so you can use it outside the original wallpaper format.

**The video is not re-encoded.** The converter decrypts the supported MLW video data and writes the original MP4 payload directly, preserving the encoded audio and video streams.

## Features

- Windows graphical interface
- Convert individual or multiple `.mlw` files
- Convert ZIP archives containing MLW files
- Optional output folder
- Drag-and-drop conversion
- No re-encoding or quality loss from transcoding

## Supported files

| | Support |
|---|---|
| Windows | Windows 10 and 11 |
| MLW format | `MLW.VIDEO`, versions 0 and 1 |
| ZIP | Archives containing supported `.mlw` files |
| `MLW.DEPTH` | Not supported |

Other MLW variants or versions may not be compatible.

## How to use

1. Install [Python 3.10 or newer](https://www.python.org/downloads/windows/). Enable **Add Python to PATH** during installation.
2. [Download the project](https://github.com/shahil5z/mlw-to-mp4-converter/archive/refs/heads/main.zip) and extract the ZIP.
3. Double-click **Open Converter.bat**.
4. Select your `.mlw` files or a ZIP archive, then click **Convert to MP4**.
5. Choose an output folder if needed. By default, converted files are saved beside the source files.

The launcher installs the required Python package automatically on first run.

### Drag and drop

Drop one or more `.mlw` or `.zip` files onto **Convert MLW files.bat**.

## Command line

You can also run the converter from PowerShell:

```powershell
py -3 mlw_to_mp4.py "C:\Wallpapers\wallpaper.mlw"
```

Choose an output folder:

```powershell
py -3 mlw_to_mp4.py "C:\Wallpapers\wallpaper.mlw" -o "C:\Converted"
```

## License

Created by **Shahil**. A Windows utility licensed under the [MIT License](LICENSE).
