import struct
from typing import List, BinaryIO, Any

from pycubex_parser.utils.exceptions import CorruptIndexError

INDEX_HEADER: bytes = b'CUBEX.INDEX'


class IndexParseResult(object):

    def __init__(self, endianness_format: str, cnode_indices: List[Any]):
        self.endianness_format = endianness_format
        self.cnode_indices = cnode_indices


def parse_index(index_file: BinaryIO) -> IndexParseResult:
    assert not index_file.closed

    header = index_file.read(len(INDEX_HEADER))
    assert header == INDEX_HEADER

    # The index file starts with the number 1 encoded as an int.
    # Here, we parse it to determine the endianness of the machine that created the index file.
    one = struct.unpack('<i', index_file.read(4))[0]

    # If the "one" is parsed as a 1, the endianness "<" format is right - else flip it.
    # Important: the endianness must also be used for the data file!
    endianness_format = '<' if one == 1 else '>'

    # IMPORTANT: not used but MUST not be deleted!
    # noinspection PyUnusedLocal
    version = struct.unpack('{}h'.format(endianness_format), index_file.read(2))[0]
    # noinspection PyUnusedLocal
    index_type = index_file.read(1)

    # Parse how many indices this file contains
    raw_size = index_file.read(4)
    n_nodes = struct.unpack('{}i'.format(endianness_format), raw_size)[0]

    raw_index = index_file.read()

    index_value_size = struct.calcsize("i")
    if len(raw_index) != index_value_size * n_nodes:
        raise CorruptIndexError(
            "The size of the index list should be equal to (size of one index value * number of nodes)."
        )

    cnode_indices = list(struct.unpack('{}{}i'.format(endianness_format, n_nodes), raw_index))
    assert len(cnode_indices) > 0
    assert index_file.peek() == b''
    return IndexParseResult(
        endianness_format=endianness_format,
        cnode_indices=cnode_indices
    )
