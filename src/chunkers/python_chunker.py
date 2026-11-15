import ast
from typing import List
from src.models import MinimalSource
from src.chunkers.base_chunker import BaseChunker, MINIMUM_THRESHOLD, OVERLAP_SIZE


class PythonChunker(BaseChunker):
    """"""

    def __init__(
            self, minimum_threshold: int = MINIMUM_THRESHOLD,
            overlap_size: int = OVERLAP_SIZE):
        super().__init__(minimum_threshold, overlap_size)

    def chunk(
            self,
            content: str,
            file_path: str, max_chunk_size: int) -> List[MinimalSource]:

        if not content or not content.strip():
            return []

        lines = content.split('\n')
        pos_start_line = []
        pos = 0

        for line in lines:
            pos_start_line.append(pos)
            pos += len(line) + 1

        fragments: list[dict[str, int | str]] = []
        try:
            tree = ast.parse(content)
            for nodo in ast.walk(tree):
                if isinstance(nodo, (ast.FunctionDef, ast.ClassDef)):
                    start_char = pos_start_line[nodo.lineno - 1]
                    nodo_end = (nodo.end_lineno if nodo.end_lineno
                                is not None else len(pos_start_line))
                    if nodo_end < len(pos_start_line):
                        fin_char = pos_start_line[nodo_end]
                    else:
                        fin_char = len(content)

                    text_function = content[start_char:fin_char]

                    if len(text_function) <= max_chunk_size:
                        self._save_fragment(
                            fragments, text_function, start_char)
                    else:
                        function_lines = text_function.split('\n')
                        current_chunk = ""
                        chunk_offset = start_char

                        for line in function_lines:
                            candidate = (
                                current_chunk + "\n" +
                                line if current_chunk else line
                            )

                            if len(candidate) <= max_chunk_size:
                                current_chunk = candidate
                            else:
                                if current_chunk:
                                    chunk_offset = self._save_fragment(
                                        fragments, current_chunk,
                                        chunk_offset)
                                if len(line) > max_chunk_size:
                                    for i in range(
                                            0, len(line), max_chunk_size):
                                        chunk_offset = self._save_fragment(
                                            fragments, line[
                                                i:i+max_chunk_size],
                                            chunk_offset)
                                    current_chunk = ""
                                else:
                                    current_chunk = line

                        if current_chunk:
                            self._save_fragment(
                                fragments, current_chunk, chunk_offset
                            )
        except SyntaxError:
            return []

        minimal_sources = []
        for chunk_data in fragments:
            source = MinimalSource(
                file_path=file_path,
                first_character_index=chunk_data['start'],
                last_character_index=chunk_data['end']
            )
            minimal_sources.append(source)
        return minimal_sources
