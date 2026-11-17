import sys
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mlw_to_mp4


class MLWDecryptorTests(unittest.TestCase):
    def make_mlw(self, mp4_payload: bytes) -> bytes:
        nonce = b"0123456789ab"
        encrypted = AESGCM(mlw_to_mp4.VIDEO_KEY).encrypt(nonce, mp4_payload, None)
        ciphertext, tag = encrypted[:-16], encrypted[-16:]
        block = nonce + (b"\x00" * 4) + ciphertext + tag
        metadata = b"test-metadata"
        return (
            b"MLW.VIDEO\x00"
            + (1).to_bytes(4, "big")
            + mlw_to_mp4.META_BLOCK_ID.to_bytes(4, "big")
            + len(metadata).to_bytes(8, "big")
            + metadata
            + mlw_to_mp4.DATA_BLOCK_ID.to_bytes(4, "big")
            + len(block).to_bytes(8, "big")
            + block
        )

    def test_decrypts_mp4_payload_without_modification(self):
        original_mp4 = b"\x00\x00\x00\x18ftypisom" + b"synthetic-test-payload"
        mlw = self.make_mlw(original_mp4)
        self.assertEqual(mlw_to_mp4.decrypt_mlw_bytes(mlw), original_mp4)

    def test_rejects_depth_file(self):
        with self.assertRaises(mlw_to_mp4.MLWError):
            mlw_to_mp4.decrypt_mlw_bytes(b"MLW.DEPTH\x00" + b"\x00" * 100)

    def test_rejects_invalid_signature(self):
        with self.assertRaises(mlw_to_mp4.MLWError):
            mlw_to_mp4.decrypt_mlw_bytes(b"NOT.MLW\x00" + b"\x00" * 100)

    def test_rejects_tampered_ciphertext(self):
        mlw = bytearray(self.make_mlw(b"\x00\x00\x00\x18ftypisomtest"))
        mlw[-20] ^= 0x01
        with self.assertRaises(mlw_to_mp4.MLWError):
            mlw_to_mp4.decrypt_mlw_bytes(bytes(mlw))


if __name__ == "__main__":
    unittest.main()
