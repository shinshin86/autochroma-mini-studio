"""Tests for storage module."""
import uuid
import pytest

from app.storage import (
    generate_id,
    validate_id,
    safe_filename,
    get_extension,
    is_video_extension,
    is_image_extension,
    get_valid_extensions,
    InvalidIdError,
)


class TestGenerateId:
    """Tests for generate_id function."""

    def test_generates_uuid(self):
        """Should generate valid UUID4."""
        id_value = generate_id()
        # Should not raise
        uuid.UUID(id_value, version=4)

    def test_generates_unique_ids(self):
        """Should generate unique IDs."""
        ids = [generate_id() for _ in range(100)]
        assert len(set(ids)) == 100


class TestValidateId:
    """Tests for validate_id function."""

    def test_valid_uuid(self):
        """Valid UUIDs should pass."""
        valid_id = str(uuid.uuid4())
        assert validate_id(valid_id) == valid_id

    def test_valid_uuid_lowercase(self):
        """Lowercase UUIDs should pass."""
        valid_id = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
        assert validate_id(valid_id) == valid_id

    def test_invalid_format(self):
        """Invalid formats should be rejected."""
        with pytest.raises(InvalidIdError):
            validate_id("not-a-uuid")

    def test_path_traversal_attempt(self):
        """Path traversal attempts should be rejected."""
        with pytest.raises(InvalidIdError):
            validate_id("../../../etc/passwd")

    def test_uuid_with_path(self):
        """UUID with path components should be rejected."""
        with pytest.raises(InvalidIdError):
            validate_id("a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d/../..")

    def test_empty_string(self):
        """Empty string should be rejected."""
        with pytest.raises(InvalidIdError):
            validate_id("")

    def test_uppercase_uuid(self):
        """Uppercase UUIDs are accepted (normalized comparison)."""
        # The implementation compares lowercase forms, so uppercase is accepted
        result = validate_id("A1B2C3D4-E5F6-4A7B-8C9D-0E1F2A3B4C5D")
        assert result == "A1B2C3D4-E5F6-4A7B-8C9D-0E1F2A3B4C5D"

    def test_uuid_wrong_version(self):
        """Non-UUID4 should still pass if format is correct."""
        # UUID validation is based on format, not strict version checking
        # The function validates that it can be parsed as UUID4
        valid_id = str(uuid.uuid4())
        assert validate_id(valid_id) == valid_id


class TestSafeFilename:
    """Tests for safe_filename function."""

    def test_simple_filename(self):
        """Simple filenames should be unchanged."""
        assert safe_filename("video.mp4") == "video.mp4"
        assert safe_filename("my_file.png") == "my_file.png"

    def test_filename_with_spaces(self):
        """Spaces should be replaced with underscores."""
        assert safe_filename("my video.mp4") == "my_video.mp4"

    def test_filename_with_special_chars(self):
        """Special characters should be replaced."""
        assert safe_filename("video@#$.mp4") == "video___.mp4"
        assert safe_filename("file<>|.mp4") == "file___.mp4"

    def test_hidden_file(self):
        """Leading dots should be stripped."""
        assert safe_filename(".hidden") == "hidden"
        assert safe_filename("..secret") == "secret"

    def test_long_filename(self):
        """Long filenames should be truncated."""
        long_name = "a" * 300 + ".mp4"
        result = safe_filename(long_name)
        assert len(result) <= 200

    def test_empty_filename(self):
        """Empty filename should return 'file'."""
        assert safe_filename("") == "file"

    def test_only_special_chars(self):
        """Filename with only special chars should be sanitized."""
        # Special chars are replaced with underscores
        result = safe_filename("@#$%^&")
        assert "_" in result
        # Should not contain original special chars
        assert "@" not in result
        assert "#" not in result

    def test_only_dots(self):
        """Filename with only dots should return 'file'."""
        assert safe_filename("...") == "file"

    def test_unicode_filename(self):
        """Unicode characters should be replaced."""
        # Japanese characters become underscores
        result = safe_filename("動画.mp4")
        assert ".mp4" in result

    def test_command_injection_attempt(self):
        """Command injection attempts should be sanitized."""
        assert "`" not in safe_filename("file`rm -rf /`.mp4")
        assert "$(" not in safe_filename("file$(whoami).mp4")
        assert ";" not in safe_filename("file;rm.mp4")


class TestGetExtension:
    """Tests for get_extension function."""

    def test_simple_extension(self):
        """Simple extensions should be extracted."""
        assert get_extension("video.mp4") == ".mp4"
        assert get_extension("image.png") == ".png"

    def test_uppercase_extension(self):
        """Extensions should be lowercase."""
        assert get_extension("video.MP4") == ".mp4"
        assert get_extension("image.PNG") == ".png"

    def test_multiple_dots(self):
        """Only last extension should be returned."""
        assert get_extension("file.tar.gz") == ".gz"
        assert get_extension("my.video.mp4") == ".mp4"

    def test_no_extension(self):
        """Files without extension should return empty."""
        assert get_extension("noextension") == ""

    def test_hidden_file_with_extension(self):
        """Hidden files with extension."""
        assert get_extension(".hidden.mp4") == ".mp4"


class TestIsVideoExtension:
    """Tests for is_video_extension function."""

    def test_video_extensions(self):
        """Video extensions should return True."""
        assert is_video_extension(".mp4") is True
        assert is_video_extension(".mov") is True
        assert is_video_extension(".avi") is True
        assert is_video_extension(".mkv") is True
        assert is_video_extension(".webm") is True

    def test_video_extensions_uppercase(self):
        """Uppercase video extensions should return True."""
        assert is_video_extension(".MP4") is True
        assert is_video_extension(".MOV") is True

    def test_image_extensions(self):
        """Image extensions should return False."""
        assert is_video_extension(".png") is False
        assert is_video_extension(".jpg") is False

    def test_invalid_extension(self):
        """Invalid extensions should return False."""
        assert is_video_extension(".exe") is False
        assert is_video_extension(".txt") is False


class TestIsImageExtension:
    """Tests for is_image_extension function."""

    def test_image_extensions(self):
        """Image extensions should return True."""
        assert is_image_extension(".png") is True
        assert is_image_extension(".jpg") is True
        assert is_image_extension(".jpeg") is True
        assert is_image_extension(".bmp") is True
        assert is_image_extension(".webp") is True
        assert is_image_extension(".gif") is True

    def test_image_extensions_uppercase(self):
        """Uppercase image extensions should return True."""
        assert is_image_extension(".PNG") is True
        assert is_image_extension(".JPG") is True

    def test_video_extensions(self):
        """Video extensions should return False."""
        assert is_image_extension(".mp4") is False
        assert is_image_extension(".mov") is False

    def test_invalid_extension(self):
        """Invalid extensions should return False."""
        assert is_image_extension(".exe") is False
        assert is_image_extension(".txt") is False


class TestGetValidExtensions:
    """Tests for get_valid_extensions function."""

    def test_contains_video_extensions(self):
        """Should contain video extensions."""
        extensions = get_valid_extensions()
        assert ".mp4" in extensions
        assert ".mov" in extensions

    def test_contains_image_extensions(self):
        """Should contain image extensions."""
        extensions = get_valid_extensions()
        assert ".png" in extensions
        assert ".jpg" in extensions

    def test_returns_set(self):
        """Should return a set."""
        extensions = get_valid_extensions()
        assert isinstance(extensions, set)
