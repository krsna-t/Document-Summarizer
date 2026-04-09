"""
SummarizationChain
------------------
Builds structured summarization prompts using LangChain's PromptTemplate.
Falls back to plain string formatting if LangChain is not installed.
"""
 
from __future__ import annotations
 
import textwrap
import logging
 
logger = logging.getLogger(__name__)
 
STYLE_INSTRUCTIONS = {
    "concise": "Write a concise summary of 3 to 5 sentences. Capture the main idea and key points only.",
    "detailed": "Write a detailed, well-structured summary in full paragraphs. Cover all major topics, arguments, and findings.",
    "bullets": "Summarize the document as a structured list of bullet points. Group related points under clear headings.",
    "executive": (
        "Write an executive brief with the following sections:\n"
        "  **TL;DR** (one sentence)\n"
        "  **Key Findings** (3-5 bullets)\n"
        "  **Recommendations** (2-3 bullets)\n"
        "  **Next Steps** (1-2 bullets)"
    ),
}
 
PROMPT_TEMPLATE = """\
You are an expert document analyst. Your task is to summarize the following document.
 
## Instructions
- Style: {style_instruction}
- Output language: {language}
- Maximum length: {max_words} words
- Be factual and accurate. Do not add information not present in the document.
- If the document is in a different language than the output language, translate as you summarize.
 
## Document Content
{document_text}
 
## Summary
"""
 
 
class SummarizationChain:
    """Builds prompts for document summarization."""
 
    def __init__(self, style: str = "concise", language: str = "English", max_words: int = 150):
        """
        Parameters
        ----------
        style     : One of 'concise', 'detailed', 'bullets', 'executive'
        language  : Output language name (e.g. 'English', 'Hindi')
        max_words : Approximate maximum word count for the summary
        """
        self.style = style
        self.language = language
        self.max_words = max_words
        self._try_init_langchain()
 
    def _try_init_langchain(self):
        try:
            # langchain >= 0.2 moved PromptTemplate to langchain-core
            try:
                from langchain_core.prompts import PromptTemplate
            except ImportError:
                from langchain.prompts import PromptTemplate
 
            self._template = PromptTemplate(
                input_variables=["style_instruction", "language", "max_words", "document_text"],
                template=PROMPT_TEMPLATE,
            )
            self._use_langchain = True
            logger.info("LangChain PromptTemplate initialized.")
        except ImportError:
            logger.warning("LangChain not installed — falling back to plain string formatting.")
            self._use_langchain = False
 
    def build_prompt(self, document_text: str) -> str:
        """
        Build the full summarization prompt.
 
        Parameters
        ----------
        document_text : Extracted text from the document
 
        Returns
        -------
        Fully formatted prompt string ready to send to an LLM.
        """
        style_instruction = STYLE_INSTRUCTIONS.get(self.style, STYLE_INSTRUCTIONS["concise"])
 
        # Truncate very long documents to avoid token limits (~12 000 chars ≈ ~3 000 tokens)
        max_chars = 12_000
        if len(document_text) > max_chars:
            document_text = document_text[:max_chars] + "\n\n[... document truncated for length ...]"
 
        if self._use_langchain:
            return self._template.format(
                style_instruction=style_instruction,
                language=self.language,
                max_words=self.max_words,
                document_text=document_text,
            )
        else:
            return PROMPT_TEMPLATE.format(
                style_instruction=style_instruction,
                language=self.language,
                max_words=self.max_words,
                document_text=document_text,
            )
 
    def chunk_text(self, text: str, chunk_size: int = 3000, overlap: int = 200) -> list[str]:
        """
        Split *text* into overlapping chunks for long-document processing.
 
        Parameters
        ----------
        chunk_size : Characters per chunk
        overlap    : Characters of overlap between chunks
        """
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += chunk_size - overlap
        return chunks
 
    def build_map_reduce_prompts(self, document_text: str) -> tuple[list[str], str]:
        """
        For very long documents, build chunk-level prompts + a final reduce prompt.
 
        Returns
        -------
        (chunk_prompts, reduce_template)
        """
        chunks = self.chunk_text(document_text)
        chunk_prompts = []
        for i, chunk in enumerate(chunks, 1):
            chunk_prompts.append(
                f"Summarize the following section ({i}/{len(chunks)}) in 3-5 sentences:\n\n{chunk}"
            )
 
        reduce_template = (
            f"The following are summaries of different sections of a document.\n"
            f"Combine them into a single {self.style} summary in {self.language} "
            f"(max {self.max_words} words):\n\n{{chunk_summaries}}"
        )
        return chunk_prompts, reduce_template
 