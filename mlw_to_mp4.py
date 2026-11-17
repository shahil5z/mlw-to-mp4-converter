#!/usr/bin/env python3
"""
MLW to MP4 Converter for Windows
Decrypts MyLiveWallpapers MLW.VIDEO files without re-encoding.
The MP4 payload is written byte-for-byte, preserving original video/audio quality.
"""

from __future__ import annotations

import argparse
import os
import struct
import sys
import zipfile
from pathlib import Path
from typing import Iterable

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    AESGCM = None


# AES-128-GCM key used by the supported MLW.VIDEO container format.
VIDEO_KEY = bytes.fromhex("d27e154628ae2ba6ab4b9775165ff737")
MAGIC_VIDEO = b"MLW.VIDEO"
META_BLOCK_ID = 0x01010101
DATA_BLOCK_ID = 0x02020202
MAX_INPUT_BYTES = 2 * 1024 * 1024 * 1024  # 2 GiB safety limit
MAX_ZIP_MEMBER_BYTES = 1024 * 1024 * 1024  # 1 GiB safety limit


class MLWError(Exception):
    pass


def u32be(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 4 > len(data):
        raise MLWError("Unexpected end of file while reading a 32-bit field.")
    return struct.unpack_from(">I", data, offset)[0]


def u64be(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 8 > len(data):
        raise MLWError("Unexpected end of file while reading a 64-bit field.")
    return struct.unpack_from(">Q", data, offset)[0]


def decrypt_mlw_bytes(data: bytes) -> bytes:
    """Return the original MP4 bytes embedded in an MLW.VIDEO file."""
    if AESGCM is None:
        raise MLWError(
            "The 'cryptography' package is missing. Close this window and run "
            "'Open Converter.bat' so it can install the dependency."
        )

    if len(data) > MAX_INPUT_BYTES:
        raise MLWError("Input exceeds the 2 GiB safety limit.")
    if len(data) <= 80:
        raise MLWError("File is too small to be a valid MLW video.")

    # Null-terminated format signature.
    null_at = data.find(b"\x00")
    if null_at < 0:
        raise MLWError("Invalid MLW header: missing null-terminated signature.")
    magic = data[:null_at]
    if magic != MAGIC_VIDEO:
        if magic == b"MLW.DEPTH":
            raise MLWError(
                "This is an MLW.DEPTH file, not a video wallpaper. "
                "It cannot be converted to MP4 as a video."
            )
        raise MLWError(f"Unsupported MLW signature: {magic!r}")

    pos = null_at + 1

    # Version (big-endian). This converter supports MLW.VIDEO versions 0 and 1.
    version = u32be(data, pos)
    pos += 4
    if version > 1:
        raise MLWError(f"Unsupported MLW version: {version}.")

    # Metadata block: ID + 64-bit byte length + metadata bytes.
    meta_id = u32be(data, pos)
    pos += 4
    if meta_id != META_BLOCK_ID:
        raise MLWError(f"Unexpected metadata block ID: 0x{meta_id:08X}.")
    meta_size = u64be(data, pos)
    pos += 8
    if meta_size > len(data) - pos:
        raise MLWError("Metadata block extends beyond the end of the file.")
    pos += meta_size

    # Encrypted video block: ID + 64-bit byte length.
    data_id = u32be(data, pos)
    pos += 4
    if data_id != DATA_BLOCK_ID:
        raise MLWError(f"Unexpected video block ID: 0x{data_id:08X}.")
    block_size = u64be(data, pos)
    pos += 8

    if block_size < 32:
        raise MLWError("Encrypted video block is too small.")
    if block_size > len(data) - pos:
        raise MLWError("Encrypted video block extends beyond the file.")
    if pos + block_size != len(data):
        # The known format stores a single encrypted block at EOF. Refuse
        # unexpected trailing bytes instead of silently discarding content.
        raise MLWError("Unexpected trailing data after the encrypted video block.")

    block = data[pos:pos + block_size]

    # Block layout: 16-byte IV field (first 12 bytes are the GCM nonce),
    # ciphertext, then the 16-byte GCM authentication tag.
    if len(block) < 32:
        raise MLWError("Invalid encrypted block layout.")
    nonce = block[:12]
    ciphertext = block[16:-16]
    tag = block[-16:]

    try:
        mp4 = AESGCM(VIDEO_KEY).decrypt(nonce, ciphertext + tag, None)
    except Exception as exc:
        raise MLWError(
            "AES-GCM authentication/decryption failed. The file may be damaged, "
            "unsupported, or not a compatible MyLiveWallpapers video."
        ) from exc

    # Basic container validation: an MP4 normally begins with an ftyp box.
    if len(mp4) < 12 or mp4[4:8] != b"ftyp":
        raise MLWError(
            "Decryption completed, but the payload does not look like an MP4 "
            "container. No output was written."
        )
    return mp4


def unique_output_path(folder: Path, stem: str) -> Path:
    candidate = folder / f"{stem}.mp4"
    if not candidate.exists():
        return candidate
    candidate = folder / f"{stem}_converted.mp4"
    if not candidate.exists():
        return candidate
    index = 2
    while True:
        candidate = folder / f"{stem}_converted_{index}.mp4"
        if not candidate.exists():
            return candidate
        index += 1


def write_converted(mlw_data: bytes, source_name: str, output_dir: Path) -> Path:
    mp4_data = decrypt_mlw_bytes(mlw_data)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = unique_output_path(output_dir, Path(source_name).stem)
    # Write atomically so a failed write never leaves a partial-looking MP4.
    temp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    try:
        with temp_path.open("wb") as handle:
            handle.write(mp4_data)
            handle.flush()
            os.fsync(handle.fileno())
        temp_path.replace(output_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()
    return output_path


def convert_path(input_path: Path, output_dir: Path) -> list[Path]:
    suffix = input_path.suffix.lower()
    if suffix == ".mlw":
        if not input_path.is_file():
            raise MLWError("Input file does not exist.")
        size = input_path.stat().st_size
        if size > MAX_INPUT_BYTES:
            raise MLWError("Input exceeds the 2 GiB safety limit.")
        return [write_converted(input_path.read_bytes(), input_path.name, output_dir)]

    if suffix == ".zip":
        outputs: list[Path] = []
        try:
            with zipfile.ZipFile(input_path, "r") as archive:
                members = [
                    item for item in archive.infolist()
                    if not item.is_dir() and item.filename.lower().endswith(".mlw")
                ]
                if not members:
                    raise MLWError("No .mlw file was found inside this ZIP.")
                for member in members:
                    if member.flag_bits & 0x1:
                        raise MLWError(f"Encrypted ZIP member is not supported: {member.filename}")
                    if member.file_size <= 0 or member.file_size > MAX_ZIP_MEMBER_BYTES:
                        raise MLWError(f"ZIP member has an invalid or excessive size: {member.filename}")
                    raw = archive.read(member)
                    # Use member basename only; never trust ZIP directory paths.
                    outputs.append(write_converted(raw, Path(member.filename).name, output_dir))
        except zipfile.BadZipFile as exc:
            raise MLWError("This file is not a valid ZIP archive.") from exc
        return outputs

    raise MLWError("Choose an .mlw file or a ZIP containing .mlw files.")


def run_cli(paths: Iterable[str], output_dir_arg: str | None) -> int:
    inputs = [Path(item.strip('"')).expanduser() for item in paths]
    if not inputs:
        return launch_gui()

    for input_path in inputs:
        try:
            out_dir = Path(output_dir_arg).expanduser() if output_dir_arg else input_path.parent
            results = convert_path(input_path, out_dir)
            for result in results:
                print(f"SUCCESS: {input_path.name} -> {result}")
        except Exception as exc:
            print(f"FAILED: {input_path}: {exc}")
    return 0


def launch_gui() -> int:
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox
    except Exception as exc:
        print(f"Could not start the Windows file picker: {exc}")
        return 1

    root = tk.Tk()
    root.title("MLW to MP4 Converter")
    root.geometry("720x470")
    root.minsize(620, 400)
    root.configure(bg="#17191f")

    title = tk.Label(
        root, text="MLW  →  MP4", font=("Segoe UI", 23, "bold"),
        fg="#f4f6fb", bg="#17191f"
    )
    title.pack(anchor="w", padx=24, pady=(22, 4))
    subtitle = tk.Label(
        root,
        text="Lossless decryption. The video is not re-encoded or resized.",
        font=("Segoe UI", 10), fg="#aeb6c5", bg="#17191f"
    )
    subtitle.pack(anchor="w", padx=26, pady=(0, 18))

    selected: list[Path] = []
    output_var = tk.StringVar(value="")
    status = tk.Text(
        root, height=12, wrap="word", bg="#222630", fg="#e8edf5",
        insertbackground="white", relief="flat", font=("Consolas", 9)
    )
    status.pack(fill="both", expand=True, padx=24, pady=(8, 12))

    def log(message: str) -> None:
        status.insert("end", message + "\n")
        status.see("end")
        root.update_idletasks()

    def choose_files() -> None:
        chosen = filedialog.askopenfilenames(
            title="Select MLW files or ZIP downloads",
            filetypes=[("MLW and ZIP files", "*.mlw *.zip"), ("All files", "*.*")]
        )
        if chosen:
            selected.clear()
            selected.extend(Path(p) for p in chosen)
            log(f"Selected {len(selected)} file(s):")
            for p in selected:
                log(f"  {p}")

    def choose_output() -> None:
        folder = filedialog.askdirectory(title="Choose MP4 output folder")
        if folder:
            output_var.set(folder)
            log(f"Output folder: {folder}")

    def convert() -> None:
        if not selected:
            messagebox.showinfo("Select files", "Choose one or more .mlw or .zip files first.")
            return
        succeeded = 0
        failed = 0
        for path in selected:
            try:
                out_dir = Path(output_var.get()) if output_var.get() else path.parent
                results = convert_path(path, out_dir)
                for result in results:
                    log(f"✓ Converted: {result}")
                    succeeded += 1
            except Exception as exc:
                log(f"✗ Failed: {path.name} — {exc}")
                failed += 1
        log(f"\nFinished. Converted: {succeeded}   Failed: {failed}")
        if succeeded:
            messagebox.showinfo(
                "Conversion finished",
                f"Converted {succeeded} file(s).\nFailed: {failed}\n\n"
                f"Output folder: {output_var.get() or selected[0].parent}"
            )
        elif failed:
            messagebox.showwarning("Conversion failed", "No files were converted. See the log for details.")

    controls = tk.Frame(root, bg="#17191f")
    controls.pack(fill="x", padx=24, pady=(0, 20))
    tk.Button(
        controls, text="1. Select MLW / ZIP files", command=choose_files,
        bg="#343c4d", fg="white", activebackground="#46516a",
        relief="flat", padx=12, pady=9
    ).pack(side="left")
    tk.Button(
        controls, text="2. Output folder (optional)", command=choose_output,
        bg="#343c4d", fg="white", activebackground="#46516a",
        relief="flat", padx=12, pady=9
    ).pack(side="left", padx=8)
    tk.Button(
        controls, text="Convert to MP4", command=convert,
        bg="#3977e8", fg="white", activebackground="#2f65c7",
        relief="flat", padx=16, pady=9, font=("Segoe UI", 9, "bold")
    ).pack(side="right")

    log("Ready. Select one or more .mlw files, or ZIP downloads containing .mlw files.")
    log("By default, MP4 files are saved beside their source files.")
    root.mainloop()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Losslessly decrypt MyLiveWallpapers .mlw video files to MP4."
    )
    parser.add_argument("files", nargs="*", help=".mlw or .zip file paths")
    parser.add_argument("-o", "--output", help="Output directory (default: beside each input)")
    args = parser.parse_args()
    return run_cli(args.files, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
