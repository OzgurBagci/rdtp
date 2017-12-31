"""Whole purpose of this script is to convert the input to binary format. In order to do that one need to specify
if it is a file or string.

It is a separate script because it may grow into something bigger if the implementation becomes complicated."""


def digest(input_data, is_file, portion):
    """Digests the input into byte sequences. Takes 3 inputs which are the data as filename or string, a boolean that
    represents if the data is file or not and how many bytes the data must be partitioned. Returns a list of byte
    arrays."""

    if is_file:
        with open(input_data, 'rb') as input_file:
            data = input_file.read()
    else:
        data = input_data.encode()

    # Every 2 characters in b' string is a byte
    if is_file:
        return [input_data.encode()] + [data[i:i+2*portion] for i in range(0, len(data), 2 * portion)]
    else:
        return [data[i:i+2 * portion] for i in range(0, len(data), 2 * portion)]
