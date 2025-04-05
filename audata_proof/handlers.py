import fingerprint

from audata_proof import db

class Uniqueness:
    def get_file_fingerprint(self, file_path: str) -> list[tuple]:
        fprint = fingerprint.Fingerprint(
            kgram_len=4, window_len=5, base=10, modulo=1000
        )
        fprint_hash: list[tuple] = fprint.generate(fpath=file_path)
        return fprint_hash

    def is_unique(self, file_path: str):
        fprint: list[tuple] = self.get_file_fingerprint(file_path)

