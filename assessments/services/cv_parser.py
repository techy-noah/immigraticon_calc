import logging
import io
from typing import Any, Optional

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
        """Extract text from PDF."""
        if not self.pdfplumber:
            return uploaded_file.read().decode('utf-8', errors='ignore')
        
        try:
            uploaded_file.seek(0)
            with self.pdfplumber.open(uploaded_file) as pdf:
                text = ''
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + '\n'
                return text if text else ''
        except Exception as e:
            logger.error(f"PDF parsing error: {e}")
            return uploaded_file.read().decode('utf-8', errors='ignore')
    
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
            
            if '@' in line and '.' in line and not info['email']:
                for word in line.split():
                    if '@' in word:
                        info['email'] = word
                        break
            
            import re
            phone_match = re.search(r'[\d\-\(\)]{10,}', line)
            if phone_match and not info['phone']:
                info['phone'] = phone_match.group()
            
            if 'education' in lower or 'degree' in lower or 'university' in lower or 'phd' in lower or 'master' in lower:
                if line and len(line) > 10:
                    info['education'].append(line)
            
            if 'experience' in lower or 'employment' in lower or 'work' in lower:
                if line and len(line) > 10:
                    info['experience'].append(line)
            
            if 'publication' in lower or 'paper' in lower or 'journal' in lower:
                if line and len(line) > 10:
                    info['publications'].append(line)
            
            if 'award' in lower or 'prize' in lower or 'recognition' in lower:
                if line and len(line) > 10:
                    info['awards'].append(line)
            
            if 'skill' in lower or 'proficient' in lower:
                if line and len(line) > 10:
                    info['skills'].append(line)
        
        info['education'] = info['education'][:5]
        info['experience'] = info['experience'][:5]
        info['publications'] = info['publications'][:10]
        info['awards'] = info['awards'][:5]
        info['skills'] = info['skills'][:10]
        
        return info