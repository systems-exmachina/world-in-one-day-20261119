"""Entry for make.fun news-image-20261119: put Thursday 19 November 2026's front page at /output/entry.png.

The picture (entry.png, beside this file) was laid out as HTML with drawn SVG art and rendered
with headless Chromium before the run; the sandbox has no network, so this program only
verifies the file against the contest's gate and writes the same bytes out every time.
"""
from pathlib import Path
import os
import struct
import zlib

SOURCE = Path(__file__).resolve().parent / "entry.png"
TARGET = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")) / "entry.png"
LIMIT_BYTES = 1 << 20
LIMIT_SIDE = 1024


def verify(blob: bytes) -> tuple[int, int]:
    """Walk every PNG chunk, test its CRC, and return (width, height)."""
    assert len(blob) <= LIMIT_BYTES, f"{len(blob)} bytes is over the 1 MiB gate"
    assert blob.startswith(b"\x89PNG\r\n\x1a\n"), "entry.png must start with the PNG signature"
    offset, size, seen_end = 8, None, False
    while offset < len(blob) and not seen_end:
        (length,) = struct.unpack_from(">I", blob, offset)
        kind = blob[offset + 4:offset + 8]
        payload = blob[offset + 8:offset + 8 + length]
        (crc,) = struct.unpack_from(">I", blob, offset + 8 + length)
        assert zlib.crc32(kind + payload) == crc, f"chunk {kind!r} has a bad CRC"
        if kind == b"IHDR":
            size = struct.unpack(">II", payload[:8])
        seen_end = kind == b"IEND"
        offset += length + 12
    assert seen_end and offset == len(blob), "entry.png must end exactly at its IEND chunk"
    assert size and max(size) <= LIMIT_SIDE, f"{size} is over 1024 x 1024"
    return size


def run() -> None:
    blob = SOURCE.read_bytes()
    width, height = verify(blob)
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_bytes(blob)
    # Read the copy back: a short or failed write must stop the run, not ship a broken image.
    assert TARGET.read_bytes() == blob, f"{TARGET} does not match entry.png after the write"
    print(f"wrote {TARGET} ({width}x{height}, {len(blob)} bytes)")


if __name__ == "__main__":
    run()
