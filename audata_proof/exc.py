"""Custom exceptions used for convenience."""

# Exceptions that are raised while checking uniqueness


class FingerprintAlreadyExists(Exception):
    pass


class TooSimilarFingerprintAlreadyExists(Exception):
    pass


class FingerprintComparisonTypeError(Exception):
    pass
