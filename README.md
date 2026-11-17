# MLW to MP4 Converter for Windows

A Windows desktop utility by **Shahil** for extracting compatible MyLiveWallpapers (`.mlw`) video wallpapers as standard MP4 files.

**No MyLiveWallpapers application required. No re-encoding.**

The converter decrypts the supported MLW video payload and writes the embedded MP4 data directly to disk. It does not resize, transcode, recompress, or change the media streams.

## Features

- Simple graphical interface for Windows
- Convert one or multiple `.mlw` video files
- Batch-convert ZIP archives containing `.mlw` files
- Drag-and-drop conversion through a Windows batch launcher
- Optional output folder selection
- Avoids overwriting existing output files
- Validates the MLW structure and AES-GCM authentication
- Leaves source files unchanged
- Command-line support for scripting

## Compatibility

| Requirement | Support |
|---|---|
| Operating system | Windows 10 / Windows 11 |
| Python | 3.10 or newer |
| MLW container | `MLW.VIDEO` |
| MLW versions | 0 and 1 |
| ZIP archives | ZIP files containing supported `.mlw` files |
| MLW.DEPTH | Not supported |

The MLW format is proprietary and may change. Other variants or newer versions may not work.

## Quick start

1. Install [Python 3](https://www.python.org/downloads/windows/) if it is not already installed. Enable **Add python.exe to PATH** during setup.
2. Download this repository using **Code → Download ZIP**, then extract it.
3. Double-click **`Open Converter.bat`**.
4. On first launch, the launcher installs the required Python dependency (`cryptography`).
5. Select one or more `.mlw` files or ZIP archives containing `.mlw` files.
6. Choose an output folder if needed, then start conversion.

Converted files are saved beside their source files by default. Existing files are never overwritten. A suffix is added when a filename already exists.

### Drag and drop

Drag one or more `.mlw` or `.zip` files onto **`Convert MLW files.bat`**.

## Command-line usage

Convert one file:

```powershell
py -3 mlw_to_mp4.py "D:\\Wallpapers\\wallpaper.mlw"
```

Choose an output directory:

```powershell
py -3 mlw_to_mp4.py "D:\\Wallpapers\\wallpaper.mlw" -o "D:\\Converted Wallpapers"
```

Convert multiple files:

```powershell
py -3 mlw_to_mp4.py "D:\\Wallpapers\\one.mlw" "D:\\Wallpapers\\two.mlw"
```

## How quality is preserved

This is a decrypt-and-extract operation, not a lossy video conversion. The decrypted MP4 payload is written directly to disk without decoding or re-encoding its audio or video streams. The encoded media data therefore remains unchanged.

This does not guarantee that every `.mlw` file is supported. Compatibility depends on the container variant and version.

## Project layout

```text
mlw-to-mp4-converter/
├── .github/
│   └── workflows/
│       └── tests.yml
├── tests/
│   └── test_converter.py
├── mlw_to_mp4.py
├── Open Converter.bat
├── Convert MLW files.bat
├── requirements.txt
├── LICENSE
├── THIRD_PARTY_NOTICES.md
├── README.md
└── .gitignore
```

## Development and tests

Install the dependency:

```powershell
py -3 -m pip install -r requirements.txt
```

Run the tests:

```powershell
py -3 -m unittest discover -s tests -v
```

The test suite creates synthetic MLW containers in memory. Wallpaper videos and other copyrighted media are not included in this repository.

## Implementation notes

The Windows application, Python interface, batch-processing workflow, ZIP handling, validation, output handling, documentation, and tests are maintained in this repository by **Shahil**.

The MLW video container parsing and decryption approach follows the publicly documented implementation in [Wallnetic](https://github.com/fatihkan/wallnetic), specifically `src/Wallnetic/Services/MLWDecryptor.swift`. That upstream implementation is credited to Fatih Kan and is MIT-licensed. The relevant notice is retained in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## Disclaimer

This is an independent community utility. It is not affiliated with, endorsed by, or supported by MyLiveWallpapers, Wallnetic, Valve, or Wallpaper Engine.

Only convert files you are authorized to access. Copyright and redistribution rights for wallpaper artwork, video, audio, and other assets remain with their respective owners. Converting a file does not grant permission to republish its contents.

The MLW format is proprietary and may change without notice. Use this software at your own risk.

## License

The original project code and documentation in this repository are released under the MIT License, copyright **2026 Shahil**, subject to the retained third-party notice for the adapted MLW decryption approach. See [`LICENSE`](LICENSE) and [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
