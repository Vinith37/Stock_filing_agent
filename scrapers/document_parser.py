"""Document parser — converts PDF, HTML, and XBRL filings to plain text"""

import httpx
import pdfplumber
import tempfile
from bs4 import BeautifulSoup
from loguru import logger


class DocumentParser:
    """Parse PDF, HTML, and XBRL documents into plain text for LLM analysis"""

    def __init__(self):
        self.client = httpx.Client(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36"
                ),
            },
        )

    def parse_document(self, url: str) -> str:
        """Download and parse a document URL into plain text

        Args:
            url: URL to the document (PDF, HTML, or XML/XBRL)

        Returns:
            Extracted text content, truncated to ~15K characters
        """
        if not url or not url.startswith("http"):
            return ""

        try:
            response = self.client.get(url)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").lower()

            if "pdf" in content_type or url.lower().endswith(".pdf"):
                return self._parse_pdf(response.content)
            elif "html" in content_type or url.lower().endswith((".html", ".htm")):
                return self._parse_html(response.text)
            elif "xml" in content_type or url.lower().endswith((".xml", ".xbrl")):
                return self._parse_xbrl(response.text)
            else:
                # Fallback: try as text
                return response.text[:10000]

        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP {e.response.status_code} fetching {url}")
            return ""
        except Exception as e:
            logger.warning(f"Failed to parse document {url}: {e}")
            return ""

    def _parse_pdf(self, content: bytes) -> str:
        """Extract text from PDF bytes using pdfplumber"""
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
                tmp.write(content)
                tmp.flush()

                text_parts = []
                with pdfplumber.open(tmp.name) as pdf:
                    # Limit to first 20 pages to avoid memory issues
                    for page in pdf.pages[:20]:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)

                full_text = "\n\n".join(text_parts)
                return full_text[:15000]  # Truncate for LLM context

        except Exception as e:
            logger.warning(f"PDF parsing failed: {e}")
            return ""

    def _parse_html(self, html: str) -> str:
        """Extract readable text from HTML content"""
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Remove non-content elements
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()

            text = soup.get_text(separator="\n", strip=True)
            return text[:15000]

        except Exception as e:
            logger.warning(f"HTML parsing failed: {e}")
            return ""

    def _parse_xbrl(self, xml_text: str) -> str:
        """Extract readable content from XBRL/XML filings"""
        try:
            soup = BeautifulSoup(xml_text, "xml")
            text = soup.get_text(separator="\n", strip=True)
            return text[:15000]

        except Exception as e:
            logger.warning(f"XBRL parsing failed: {e}")
            return ""

    def close(self):
        """Close the HTTP client"""
        self.client.close()
