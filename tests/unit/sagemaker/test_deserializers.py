# Copyright 2017-2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
from __future__ import absolute_import

import io

import numpy as np
import pytest

from sagemaker.deserializers import (
    StringDeserializer,
    BytesDeserializer,
    CSVDeserializer,
    StreamDeserializer,
    NumpyDeserializer,
    JSONDeserializer,
)


def test_string_deserializer():
    deserializer = StringDeserializer()

    result = deserializer.deserialize(io.BytesIO(b"[1, 2, 3]"), "application/json")

    assert result == "[1, 2, 3]"


def test_bytes_deserializer():
    deserializer = BytesDeserializer()

    result = deserializer.deserialize(io.BytesIO(b"[1, 2, 3]"), "application/json")

    assert result == b"[1, 2, 3]"


@pytest.fixture
def csv_deserializer():
    return CSVDeserializer()


def test_csv_deserializer_single_element(csv_deserializer):
    result = csv_deserializer.deserialize(io.BytesIO(b"1"), "text/csv")
    assert result == [["1"]]


def test_csv_deserializer_array(csv_deserializer):
    result = csv_deserializer.deserialize(io.BytesIO(b"1,2,3"), "text/csv")
    assert result == [["1", "2", "3"]]


def test_csv_deserializer_2dimensional(csv_deserializer):
    result = csv_deserializer.deserialize(io.BytesIO(b"1,2,3\n3,4,5"), "text/csv")
    assert result == [["1", "2", "3"], ["3", "4", "5"]]


def test_csv_deserializer_posix_compliant(csv_deserializer):
    result = csv_deserializer.deserialize(io.BytesIO(b"1,2,3\n3,4,5\n"), "text/csv")
    assert result == [["1", "2", "3"], ["3", "4", "5"]]


def test_stream_deserializer():
    deserializer = StreamDeserializer()

    stream, content_type = deserializer.deserialize(io.BytesIO(b"[1, 2, 3]"), "application/json")
    try:
        result = stream.read()
    finally:
        stream.close()

    assert result == b"[1, 2, 3]"
    assert content_type == "application/json"


@pytest.fixture
def numpy_deserializer():
    return NumpyDeserializer()


def test_numpy_deserializer_from_csv(numpy_deserializer):
    stream = io.BytesIO(b"1,2,3\n4,5,6")
    array = numpy_deserializer.deserialize(stream, "text/csv")
    assert np.array_equal(array, np.array([[1, 2, 3], [4, 5, 6]]))


def test_numpy_deserializer_from_csv_ragged(numpy_deserializer):
    stream = io.BytesIO(b"1,2,3\n4,5,6,7")
    with pytest.raises(ValueError) as error:
        numpy_deserializer.deserialize(stream, "text/csv")
    assert "errors were detected" in str(error)


def test_numpy_deserializer_from_csv_alpha():
    numpy_deserializer = NumpyDeserializer(dtype="U5")
    stream = io.BytesIO(b"hello,2,3\n4,5,6")
    array = numpy_deserializer.deserialize(stream, "text/csv")
    assert np.array_equal(array, np.array([["hello", 2, 3], [4, 5, 6]]))


def test_numpy_deserializer_from_json(numpy_deserializer):
    stream = io.BytesIO(b"[[1,2,3],\n[4,5,6]]")
    array = numpy_deserializer.deserialize(stream, "application/json")
    assert np.array_equal(array, np.array([[1, 2, 3], [4, 5, 6]]))


# Sadly, ragged arrays work fine in JSON (giving us a 1D array of Python lists)
def test_numpy_deserializer_from_json_ragged(numpy_deserializer):
    stream = io.BytesIO(b"[[1,2,3],\n[4,5,6,7]]")
    array = numpy_deserializer.deserialize(stream, "application/json")
    assert np.array_equal(array, np.array([[1, 2, 3], [4, 5, 6, 7]]))


def test_numpy_deserializer_from_json_alpha():
    numpy_deserializer = NumpyDeserializer(dtype="U5")
    stream = io.BytesIO(b'[["hello",2,3],\n[4,5,6]]')
    array = numpy_deserializer.deserialize(stream, "application/json")
    assert np.array_equal(array, np.array([["hello", 2, 3], [4, 5, 6]]))


def test_numpy_deserializer_from_npy(numpy_deserializer):
    array = np.ones((2, 3))
    stream = io.BytesIO()
    np.save(stream, array)
    stream.seek(0)

    result = numpy_deserializer.deserialize(stream, "application/x-npy")

    assert np.array_equal(array, result)


def test_numpy_deserializer_from_npy_object_array(numpy_deserializer):
    array = np.array(["one", "two"])
    stream = io.BytesIO()
    np.save(stream, array)
    stream.seek(0)

    result = numpy_deserializer.deserialize(stream, "application/x-npy")

    assert np.array_equal(array, result)


@pytest.fixture
def json_deserializer():
    return JSONDeserializer()


def test_json_deserializer_array(json_deserializer):
    result = json_deserializer.deserialize(io.BytesIO(b"[1, 2, 3]"), "application/json")

    assert result == [1, 2, 3]


def test_json_deserializer_2dimensional(json_deserializer):
    result = json_deserializer.deserialize(
        io.BytesIO(b"[[1, 2, 3], [3, 4, 5]]"), "application/json"
    )

    assert result == [[1, 2, 3], [3, 4, 5]]


def test_json_deserializer_invalid_data(json_deserializer):
    with pytest.raises(ValueError) as error:
        json_deserializer.deserialize(io.BytesIO(b"[[1]"), "application/json")
    assert "column" in str(error)
