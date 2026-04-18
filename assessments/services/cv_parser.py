import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CVParser:
    """Parse CV/resume to extract structured information."""
    
    def __init__(self):
        self.pdfplumber = None
        self.docx = None
        
        try:
            import pdfplumber
            self.pdfplumber = pdfplumber
        except ImportError:
            pass
        
        try:
            from docx import Document
            self.Document = Document
        except ImportError:
            pass
    
    def parse_file(self, uploaded_file) -> Optional[str]:
        """Parse uploaded CV file and return text content."""
        try:
            filename = uploaded_file.name.lower()
            
            if filename.endswith('.pdf'):
                return self._parse_pdf(uploaded_file)
            elif filename.endswith('.docx'):
                return self._parse_docx(uploaded_file)
            elif filename.endswith('.txt'):
                return uploaded_file.read().decode('utf-8', errors='ignore')
            else:
                logger.warning(f"Unsupported file type: {filename}")
                return None
                
        except Exception as e:
            logger.error(f"CV parsing failed: {e}")
            return None
    
    def _parse_pdf(self, uploaded_file) -> str:
        """Extract text from PDF using available library."""
        # Try PyPDF2 first (simpler, no C extensions)
        try:
            import PyPDF2
            uploaded_file.seek(0)
            reader = PyPDF2.PdfReader(uploaded_file)
            text = ''
            for page in reader.pages:
                text += page.extract_text() + '\n'
            if text.strip():
                return text
        except Exception as e:
            logger.debug(f"PyPDF2 failed: {e}")
        
        # Fallback: just read raw bytes as text (will be garbage but won't crash)
        try:
            uploaded_file.seek(0)
            content = uploaded_file.read()
            # Try to extract readable text from PDF raw
            text_parts = []
            for line in content.split(b'\n'):
                try:
                    decoded = line.decode('utf-8', errors='ignore')
                    if len(decoded) > 20 and len(decoded) < 200:
                        text_parts.append(decoded)
                except:
                    pass
            return '\n'.join(text_parts[:500])
        except:
            pass
        
        return "Could not parse PDF. Please upload as text or Word document."
    
    def _parse_docx(self, uploaded_file) -> str:
        """Extract text from DOCX."""
        if not self.Document:
            return ''
        
        try:
            uploaded_file.seek(0)
            doc = self.Document(uploaded_file)
            text = ''
            for para in doc.paragraphs:
                if para.text.strip():
                    text += para.text + '\n'
            return text
        except Exception as e:
            logger.error(f"DOCX parsing error: {e}")
            return ''
    
    def extract_key_info(self, text: str) -> dict:
        """Extract key information from CV text."""
        import re
        
        info = {
            'name': '',
            'email': '',
            'phone': '',
            'education': [],
            'experience': [],
            'publications': [],
            'awards': [],
            'skills': [],
            'summary': ''
        }
        
        if not text:
            return info
        
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            lower = line.lower()
            
            # Extract email
            if '@' in line and '.' in line and not info['email']:
                for word in line.split():
                    if '@' in word and '.' in word:
                        info['email'] = word
                        break
            
            # Extract phone
            phone_match = re.search(r'[\d\-\(\)]{10,}', line)
            if phone_match and not info['phone']:
                info['phone'] = phone_match.group()
            
            # Categorize content
            if any(kw in lower for kw in ['education', 'degree', 'university', 'phd', 'master', 'bachelor', 'college']):
                if line and len(line) > 10:
                    info['education'].append(line)
            
            elif any(kw in lower for kw in ['experience', 'employment', 'work history', 'position', 'role']):
                if line and len(line) > 10:
                    info['experience'].append(line)
            
            elif any(kw in lower for kw in ['publication', 'paper', 'journal', 'conference', 'presented']):
                if line and len(line) > 10:
                    info['publications'].append(line)
            
            elif any(kw in lower for kw in ['award', 'prize', 'recognition', 'honor', 'grant']):
                if line and len(line) > 10:
                    info['awards'].append(line)
        
        # Limit entries
        info['education'] = info['education'][:5]
        info['experience'] = info['experience'][:5]
        info['publications'] = info['publications'][:10]
        info['awards'] = info['awards'][:5]
        info['skills'] = info['skills'][:10]
        
        return info