import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CVParser:
    """Parse CV/resume - simplified version for deployment."""
    
    def __init__(self):
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
        """Extract text from PDF using PyPDF2."""
        try:
            import PyPDF2
            uploaded_file.seek(0)
            reader = PyPDF2.PdfReader(uploaded_file)
            text = ''
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + '\n'
            if text.strip():
                return text
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"PDF parsing: {e}")
        
        # Fallback: return file info
        return f"[PDF file: {uploaded_file.name}]"
    
    def _parse_docx(self, uploaded_file) -> str:
        """Extract text from DOCX."""
        try:
            from docx import Document
            uploaded_file.seek(0)
            doc = Document(uploaded_file)
            text = ''
            for para in doc.paragraphs:
                if para.text.strip():
                    text += para.text + '\n'
            return text
        except ImportError:
            return "[Unable to parse DOCX - docx not installed]"
        except Exception as e:
            logger.debug(f"DOCX parsing: {e}")
            return f"[DOCX file: {uploaded_file.name}]"
    
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
        }
        
        if not text:
            return info
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            lower = line.lower()
            
            if '@' in line and '.' in line and not info['email']:
                for word in line.split():
                    if '@' in word and '.' in word:
                        info['email'] = word
                        break
            
            phone_match = re.search(r'[\d\-\(\)]{10,}', line)
            if phone_match and not info['phone']:
                info['phone'] = phone_match.group()
            
            if any(kw in lower for kw in ['education', 'degree', 'university', 'phd', 'master', 'bachelor']):
                if line and len(line) > 10:
                    info['education'].append(line)
            elif any(kw in lower for kw in ['experience', 'employment', 'position', 'role']):
                if line and len(line) > 10:
                    info['experience'].append(line)
            elif any(kw in lower for kw in ['publication', 'journal', 'conference']):
                if line and len(line) > 10:
                    info['publications'].append(line)
            elif any(kw in lower for kw in ['award', 'prize', 'honor']):
                if line and len(line) > 10:
                    info['awards'].append(line)
        
        info['education'] = info['education'][:5]
        info['experience'] = info['experience'][:5]
        info['publications'] = info['publications'][:10]
        info['awards'] = info['awards'][:5]
        
        return info