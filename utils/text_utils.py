"""
Utilitários para processamento de texto.
"""
import re
from bs4 import BeautifulSoup


def bs4_extractor(html: str) -> str:
    """
    Extrai texto limpo do HTML usando BeautifulSoup e normaliza quebras de linha.
    
    Args:
        html: Conteúdo HTML a ser processado
        
    Returns:
        str: Texto limpo extraído do HTML
    """
    soup = BeautifulSoup(html, "lxml")
    
    # Remove tags script, style e noscript
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()
    
    # Extrai texto com separadores de linha
    text = soup.get_text(separator="\n")
    
    # Normaliza espaços em branco antes de quebras de linha
    text = re.sub(r"\s+\n", "\n", text)
    
    # Normaliza múltiplas quebras de linha consecutivas
    text = re.sub(r"\n{2,}", "\n\n", text).strip()
    
    return text