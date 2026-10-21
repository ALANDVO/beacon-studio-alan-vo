from dataclasses import dataclass, field
from typing import Optional
import json
from pathlib import Path


@dataclass
class ContextSection:
    title: str
    content: str
    source: str = "interview"  # "interview" | "document" | "inferred"
    is_unknown: bool = False


@dataclass
class ContextPack:
    name: str
    company_name: str
    description: str
    sections: list[ContextSection] = field(default_factory=list)

    def to_files(self, output_dir: Path) -> list[str]:
        """Write context pack files to output directory."""
        output_dir.mkdir(parents=True, exist_ok=True)
        written = []

        # Write main context file
        main_content = self._generate_main_content()
        main_file = output_dir / "company_context.md"
        main_file.write_text(main_content, encoding="utf-8")
        written.append(str(main_file))

        # Write individual section files
        for i, section in enumerate(self.sections):
            section_file = output_dir / f"{i+1:02d}_{section.title.lower().replace(' ', '_')}.md"
            content = f"# {section.title}\n\n"
            if section.is_unknown:
                content += "> ⚠️ **Unknown/Unsourced**: This section contains inferred or unverified information.\n\n"
            content += f"**Source**: {section.source}\n\n"
            content += section.content
            section_file.write_text(content, encoding="utf-8")
            written.append(str(section_file))

        return written

    def _generate_main_content(self) -> str:
        lines = [
            f"# {self.company_name} - Company Context",
            f"\n{self.description}\n",
            "## Sections\n",
        ]
        for section in self.sections:
            marker = " ⚠️" if section.is_unknown else ""
            lines.append(f"- [{section.title}](./{section.title.lower().replace(' ', '_')}.md){marker} ({section.source})")
        return "\n".join(lines)


DEFAULT_QUESTIONS = [
    {"key": "company_name", "question": "What is your company name?", "required": True},
    {"key": "description", "question": "Describe your company in 2-3 sentences.", "required": True},
    {"key": "target_market", "question": "Who is your target market? (ICP, company size, industry)", "required": True},
    {"key": "value_prop", "question": "What is your core value proposition?", "required": True},
    {"key": "pricing", "question": "What is your pricing model?", "required": False},
    {"key": "competitors", "question": "Who are your main competitors?", "required": False},
    {"key": "differentiators", "question": "What are your key differentiators?", "required": False},
    {"key": "go_to_market", "question": "Describe your go-to-market motion.", "required": False},
    {"key": "team", "question": "Describe your team structure and key roles.", "required": False},
    {"key": "metrics", "question": "What are your key metrics (ARR, users, growth)?", "required": False},
]


def generate_context_pack(answers: dict[str, str]) -> ContextPack:
    """Generate a ContextPack from interview answers."""
    company_name = answers.get("company_name", "Unknown Company")
    description = answers.get("description", "")

    sections = []
    for q in DEFAULT_QUESTIONS:
        key = q["key"]
        answer = answers.get(key, "").strip()
        if answer:
            sections.append(ContextSection(
                title=key.replace("_", " ").title(),
                content=answer,
                source="interview",
                is_unknown=False,
            ))
        elif q["required"]:
            sections.append(ContextSection(
                title=key.replace("_", " ").title(),
                content="[UNKNOWN - Required field not provided]",
                source="inferred",
                is_unknown=True,
            ))

    return ContextPack(
        name=f"{company_name} Context Pack",
        company_name=company_name,
        description=description,
        sections=sections,
    )