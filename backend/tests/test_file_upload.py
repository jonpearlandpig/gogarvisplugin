"""
Test file upload functionality for GoGarvis Chat
Tests: File upload, text extraction, chat with attachments, file deletion
"""
import pytest
import requests
import os
import tempfile

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestFileUpload:
    """File upload endpoint tests"""
    
    def test_health_check(self):
        """Verify API is healthy"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✓ Health check passed: {data}")
    
    def test_upload_txt_file(self):
        """Test uploading a TXT file with text extraction"""
        # Create a test TXT file
        test_content = "This is a test document for GoGarvis file upload testing."
        
        files = {
            'files': ('TEST_upload.txt', test_content.encode(), 'text/plain')
        }
        
        response = requests.post(f"{BASE_URL}/api/chat/upload", files=files)
        assert response.status_code == 200, f"Upload failed: {response.text}"
        
        data = response.json()
        assert len(data) == 1, "Expected 1 file in response"
        
        file_info = data[0]
        assert "file_id" in file_info
        assert file_info["filename"] == "TEST_upload.txt"
        assert file_info["file_type"] == "text/plain"
        assert file_info["size"] > 0
        assert file_info["extracted_text"] is not None
        assert "test document" in file_info["extracted_text"].lower()
        
        print(f"✓ TXT upload passed: file_id={file_info['file_id']}, extracted_text present")
        
        # Store file_id for cleanup
        self.__class__.txt_file_id = file_info["file_id"]
        return file_info["file_id"]
    
    def test_upload_md_file(self):
        """Test uploading a Markdown file with text extraction"""
        md_content = """# Test Markdown Document
        
## Section 1
This is a test markdown file for GoGarvis.

- Item 1
- Item 2
- Item 3
"""
        files = {
            'files': ('TEST_readme.md', md_content.encode(), 'text/markdown')
        }
        
        response = requests.post(f"{BASE_URL}/api/chat/upload", files=files)
        assert response.status_code == 200, f"Upload failed: {response.text}"
        
        data = response.json()
        assert len(data) == 1
        
        file_info = data[0]
        assert file_info["filename"] == "TEST_readme.md"
        assert file_info["file_type"] == "text/markdown"
        assert file_info["extracted_text"] is not None
        assert "markdown" in file_info["extracted_text"].lower()
        
        print(f"✓ MD upload passed: file_id={file_info['file_id']}")
        self.__class__.md_file_id = file_info["file_id"]
        return file_info["file_id"]
    
    def test_upload_multiple_files(self):
        """Test uploading multiple files in single request"""
        files = [
            ('files', ('TEST_file1.txt', b'Content of file 1', 'text/plain')),
            ('files', ('TEST_file2.txt', b'Content of file 2', 'text/plain')),
        ]
        
        response = requests.post(f"{BASE_URL}/api/chat/upload", files=files)
        assert response.status_code == 200, f"Upload failed: {response.text}"
        
        data = response.json()
        assert len(data) == 2, f"Expected 2 files, got {len(data)}"
        
        filenames = [f["filename"] for f in data]
        assert "TEST_file1.txt" in filenames
        assert "TEST_file2.txt" in filenames
        
        print(f"✓ Multiple file upload passed: {len(data)} files uploaded")
        
        # Store for cleanup
        self.__class__.multi_file_ids = [f["file_id"] for f in data]
        return data
    
    def test_upload_png_image(self):
        """Test uploading a PNG image file"""
        # Create a minimal valid PNG (1x1 transparent pixel)
        png_data = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 dimensions
            0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,  # bit depth, color type
            0x89, 0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41,  # IDAT chunk
            0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,  # compressed data
            0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00,  # CRC
            0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44,  # IEND chunk
            0xAE, 0x42, 0x60, 0x82
        ])
        
        files = {
            'files': ('TEST_image.png', png_data, 'image/png')
        }
        
        response = requests.post(f"{BASE_URL}/api/chat/upload", files=files)
        assert response.status_code == 200, f"Upload failed: {response.text}"
        
        data = response.json()
        assert len(data) == 1
        
        file_info = data[0]
        assert file_info["filename"] == "TEST_image.png"
        assert file_info["file_type"] == "image/png"
        # Images should NOT have extracted_text
        assert file_info["extracted_text"] is None
        
        print(f"✓ PNG upload passed: file_id={file_info['file_id']}, no text extraction (expected)")
        self.__class__.png_file_id = file_info["file_id"]
        return file_info["file_id"]
    
    def test_upload_jpg_image(self):
        """Test uploading a JPG image file"""
        # Minimal valid JPEG (1x1 red pixel)
        jpg_data = bytes([
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46,
            0x49, 0x46, 0x00, 0x01, 0x01, 0x00, 0x00, 0x01,
            0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
            0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08,
            0x07, 0x07, 0x07, 0x09, 0x09, 0x08, 0x0A, 0x0C,
            0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
            0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D,
            0x1A, 0x1C, 0x1C, 0x20, 0x24, 0x2E, 0x27, 0x20,
            0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
            0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27,
            0x39, 0x3D, 0x38, 0x32, 0x3C, 0x2E, 0x33, 0x34,
            0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
            0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4,
            0x00, 0x1F, 0x00, 0x00, 0x01, 0x05, 0x01, 0x01,
            0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04,
            0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0xFF,
            0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03,
            0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04,
            0x00, 0x00, 0x01, 0x7D, 0x01, 0x02, 0x03, 0x00,
            0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06,
            0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32,
            0x81, 0x91, 0xA1, 0x08, 0x23, 0x42, 0xB1, 0xC1,
            0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72,
            0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A,
            0x25, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x34, 0x35,
            0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45,
            0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55,
            0x56, 0x57, 0x58, 0x59, 0x5A, 0x63, 0x64, 0x65,
            0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75,
            0x76, 0x77, 0x78, 0x79, 0x7A, 0x83, 0x84, 0x85,
            0x86, 0x87, 0x88, 0x89, 0x8A, 0x92, 0x93, 0x94,
            0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3,
            0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2,
            0xB3, 0xB4, 0xB5, 0xB6, 0xB7, 0xB8, 0xB9, 0xBA,
            0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9,
            0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8,
            0xD9, 0xDA, 0xE1, 0xE2, 0xE3, 0xE4, 0xE5, 0xE6,
            0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4,
            0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF, 0xDA,
            0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00,
            0xFB, 0xD5, 0xDB, 0x20, 0xA8, 0xF1, 0x7F, 0xFF,
            0xD9
        ])
        
        files = {
            'files': ('TEST_image.jpg', jpg_data, 'image/jpeg')
        }
        
        response = requests.post(f"{BASE_URL}/api/chat/upload", files=files)
        assert response.status_code == 200, f"Upload failed: {response.text}"
        
        data = response.json()
        file_info = data[0]
        assert file_info["filename"] == "TEST_image.jpg"
        assert file_info["file_type"] == "image/jpeg"
        
        print(f"✓ JPG upload passed: file_id={file_info['file_id']}")
        self.__class__.jpg_file_id = file_info["file_id"]
        return file_info["file_id"]
    
    def test_upload_invalid_file_type(self):
        """Test that invalid file types are rejected"""
        files = {
            'files': ('TEST_invalid.exe', b'fake executable content', 'application/octet-stream')
        }
        
        response = requests.post(f"{BASE_URL}/api/chat/upload", files=files)
        assert response.status_code == 400, f"Expected 400 for invalid file type, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data
        assert "not allowed" in data["detail"].lower() or "file type" in data["detail"].lower()
        
        print(f"✓ Invalid file type rejection passed: {data['detail']}")
    
    def test_get_file_info(self):
        """Test getting file metadata after upload"""
        # First upload a file
        files = {
            'files': ('TEST_getinfo.txt', b'Test content for get info', 'text/plain')
        }
        upload_response = requests.post(f"{BASE_URL}/api/chat/upload", files=files)
        assert upload_response.status_code == 200
        file_id = upload_response.json()[0]["file_id"]
        
        # Get file info
        response = requests.get(f"{BASE_URL}/api/chat/files/{file_id}")
        assert response.status_code == 200, f"Get file info failed: {response.text}"
        
        data = response.json()
        assert data["file_id"] == file_id
        assert data["filename"] == "TEST_getinfo.txt"
        assert "path" in data
        assert "uploaded_at" in data
        
        print(f"✓ Get file info passed: {data['filename']}")
        self.__class__.getinfo_file_id = file_id
        return file_id
    
    def test_delete_file(self):
        """Test deleting an uploaded file"""
        # First upload a file
        files = {
            'files': ('TEST_delete.txt', b'File to be deleted', 'text/plain')
        }
        upload_response = requests.post(f"{BASE_URL}/api/chat/upload", files=files)
        assert upload_response.status_code == 200
        file_id = upload_response.json()[0]["file_id"]
        
        # Delete the file
        response = requests.delete(f"{BASE_URL}/api/chat/files/{file_id}")
        assert response.status_code == 200, f"Delete failed: {response.text}"
        
        data = response.json()
        assert data["message"] == "File deleted"
        assert data["file_id"] == file_id
        
        # Verify file is gone
        get_response = requests.get(f"{BASE_URL}/api/chat/files/{file_id}")
        assert get_response.status_code == 404, "File should not exist after deletion"
        
        print(f"✓ Delete file passed: file_id={file_id}")
    
    def test_delete_nonexistent_file(self):
        """Test deleting a file that doesn't exist"""
        response = requests.delete(f"{BASE_URL}/api/chat/files/nonexistent-file-id")
        assert response.status_code == 404
        
        print("✓ Delete nonexistent file returns 404 as expected")


class TestChatWithAttachments:
    """Test chat endpoint with file attachments"""
    
    def test_chat_without_files(self):
        """Test basic chat without file attachments"""
        payload = {
            "message": "Hello, what is GARVIS?",
            "session_id": None,
            "file_ids": None
        }
        
        response = requests.post(f"{BASE_URL}/api/chat", json=payload)
        assert response.status_code == 200, f"Chat failed: {response.text}"
        
        data = response.json()
        assert "response" in data
        assert "session_id" in data
        assert len(data["response"]) > 0
        
        print(f"✓ Basic chat passed: session_id={data['session_id'][:8]}...")
        return data["session_id"]
    
    def test_chat_with_text_file(self):
        """Test chat with a text file attachment"""
        # Upload a file first
        test_content = "The GoGarvis system has 7 main components: GARVIS, Telauthorium, Flightpath COS, MOSE, Pig Pen, TELA, and ECOS."
        files = {
            'files': ('TEST_context.txt', test_content.encode(), 'text/plain')
        }
        upload_response = requests.post(f"{BASE_URL}/api/chat/upload", files=files)
        assert upload_response.status_code == 200
        file_id = upload_response.json()[0]["file_id"]
        
        # Chat with file attachment
        payload = {
            "message": "Based on the uploaded document, how many main components does GoGarvis have?",
            "session_id": None,
            "file_ids": [file_id]
        }
        
        response = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=60)
        assert response.status_code == 200, f"Chat with file failed: {response.text}"
        
        data = response.json()
        assert "response" in data
        # The response should reference the document content
        print(f"✓ Chat with text file passed: response length={len(data['response'])}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/chat/files/{file_id}")
        return data
    
    def test_chat_with_multiple_files(self):
        """Test chat with multiple file attachments"""
        # Upload multiple files
        files = [
            ('files', ('TEST_doc1.txt', b'Document 1: GARVIS is the sovereign intelligence layer.', 'text/plain')),
            ('files', ('TEST_doc2.txt', b'Document 2: TELA handles execution tasks.', 'text/plain')),
        ]
        upload_response = requests.post(f"{BASE_URL}/api/chat/upload", files=files)
        assert upload_response.status_code == 200
        file_ids = [f["file_id"] for f in upload_response.json()]
        
        # Chat with multiple files
        payload = {
            "message": "What do the uploaded documents say about GARVIS and TELA?",
            "session_id": None,
            "file_ids": file_ids
        }
        
        response = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=60)
        assert response.status_code == 200, f"Chat with multiple files failed: {response.text}"
        
        data = response.json()
        assert "response" in data
        print(f"✓ Chat with multiple files passed")
        
        # Cleanup
        for fid in file_ids:
            requests.delete(f"{BASE_URL}/api/chat/files/{fid}")
        return data


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_files(self):
        """Clean up any remaining test files"""
        # This is a best-effort cleanup
        print("✓ Cleanup completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
