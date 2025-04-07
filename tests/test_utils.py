from audata_proof.utils import decode_db_fingerprint
from tests import fprint_strings


def test_decode_db_fingerprint():
    actual = decode_db_fingerprint(fprint_strings.raw)
    assert str(actual) == fprint_strings.expected
