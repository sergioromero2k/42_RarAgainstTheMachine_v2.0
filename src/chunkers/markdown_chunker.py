from src.chunkers.base_chunker import BaseChunker
from typing import List
from src.models import MinimalSource
import re


class MarkdownChunker(BaseChunker):
    """"""

    def __init__(self, minimum_threshold: int = 100, overlap_size: int = 200):
        super().__init__(minimum_threshold, overlap_size)
        self.heading_pattern = re.compile(r'^[ ]{0,3}#{1,6}\s+', re.MULTILINE)

    def _split_long_text(
            self,
            text: str,
            base_start: int,
            max_chunk_size: int) -> List[dict]:
        """"""
        fragments: list[dict[str, int | str]] = []
        parts = re.split(r'(\.)', text)
        sentences_info = []
        temp_current_sentence = ""

        for part in parts:
            temp_current_sentence += part
            if part == '.':
                sentences_info.append(temp_current_sentence)
                temp_current_sentence = ""

        if temp_current_sentence:
            sentences_info.append(temp_current_sentence)

        temp_chunk = ""
        chunk_start_offset = base_start

        for sentence in sentences_info:
            if len(sentence) > max_chunk_size:
                if temp_chunk:
                    chunk_start_offset = self._save_fragment(
                        fragments, temp_chunk, chunk_start_offset)
                    temp_chunk = ""

                words = re.split(r'(\s+)', sentence)
                emergency_chunk = ""

                for word in words:
                    if len(word) > max_chunk_size:
                        if emergency_chunk:
                            chunk_start_offset = self._save_fragment(
                                fragments, emergency_chunk, chunk_start_offset)
                            emergency_chunk = ""

                        for i in range(0, len(word), max_chunk_size):
                            char_chunk = word[i: i + max_chunk_size]
                            chunk_start_offset = self._save_fragment(
                                fragments, char_chunk, chunk_start_offset)
                    elif len(emergency_chunk) + len(word) <= max_chunk_size:
                        emergency_chunk += word
                    else:
                        if emergency_chunk:
                            chunk_start_offset = self._save_fragment(
                                fragments, emergency_chunk, chunk_start_offset)
                            emergency_chunk = word

                if emergency_chunk:
                    chunk_start_offset = self._save_fragment(
                        fragments, emergency_chunk, chunk_start_offset)
            else:
                if len(temp_chunk) + len(sentence) <= max_chunk_size:
                    temp_chunk += sentence
                else:
                    if temp_chunk:
                        chunk_start_offset = self._save_fragment(
                            fragments, temp_chunk, chunk_start_offset)
                    temp_chunk = sentence
        if temp_chunk:
            chunk_start_offset = self._save_fragment(
                fragments, temp_chunk, chunk_start_offset)

        return fragments

    def chunk(
            self,
            content: str,
            file_path: str, max_chunk_size: int) -> List[MinimalSource]:

        if not content or not content.strip():
            return []

        sections = []
        matches = list(self.heading_pattern.finditer(content))

        if not matches:
            sections.append({
                'text': content,
                'start': 0,
                'end': len(content)
            })
        else:
            if matches[0].start() > 0:
                sections.append({
                    'text': content[:matches[0].start()],
                    'start': 0,
                    'end': matches[0].start()
                })

            for i, match in enumerate(matches):
                start_pos = match.start()
                end_pos = matches[i+1].start() if i + \
                    1 < len(matches) else len(content)

                section_text = content[start_pos:end_pos]
                sections.append({
                    'text': section_text,
                    'start': start_pos,
                    'end': end_pos
                })

        candidate_fragments = []
        for section in sections:
            section_text = section['text']
            base_start = section['start']

            if len(section_text) <= max_chunk_size:
                candidate_fragments.append({
                    'text': section_text,
                    'start': base_start,
                    'end': base_start + len(section_text)
                })
            else:
                sub_fragments = self._split_long_text(
                    section_text, base_start, max_chunk_size)
                candidate_fragments.extend(sub_fragments)

        merged_chunks = []
        for candidate in candidate_fragments:
            if (merged_chunks and
                    len(merged_chunks[-1]['text']) < self.minimum_threshold):
                combined_text = merged_chunks[-1]['text'] + candidate['text']
                if len(combined_text) <= max_chunk_size:
                    merged_chunks[-1]['text'] = combined_text
                    merged_chunks[-1]['end'] = candidate['end']
                else:
                    merged_chunks.append(candidate)
            else:
                merged_chunks.append(candidate)

        original_starts = [c['start'] for c in merged_chunks]
        for i in range(1, len(merged_chunks)):
            chunk = merged_chunks[i]

            new_start = max(0, original_starts[i] - self.overlap_size)
            new_start = max(original_starts[i - 1], new_start)
            new_start = max(new_start, chunk['end'] - max_chunk_size)

            chunk['text'] = content[new_start: chunk['end']]
            chunk['start'] = new_start

        minimal_sources = []
        for chunk_data in merged_chunks:
            source = MinimalSource(
                file_path=file_path,
                first_character_index=chunk_data['start'],
                last_character_index=chunk_data['end']
            )
            minimal_sources.append(source)

        return minimal_sources
