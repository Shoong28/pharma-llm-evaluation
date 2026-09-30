"""
Filter DrugBank XML to retain only selected fields.

This script reads a DrugBank XML file and extracts a subset of fields for each
<drug> element. The goal is to reduce context length by keeping only
information relevant to question generation. It retains the drug name,
description, mechanism of action, pharmacodynamics, indications,
classification, affected organisms, and toxicity. Drug interactions and
other fields are discarded.

The filtered output is written to a JSON Lines (.jsonl) file where each
line represents a single drug entry with the selected fields.

Usage:

    python filter_drugbank.py --input path/to/drugbank.xml \
                              --output filtered_drugbank.jsonl

Because DrugBank XML files can be very large, this script uses an
incremental ``iterparse`` approach to avoid loading the entire XML
document into memory at once.
"""

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional


def extract_text(elem: Optional[ET.Element]) -> Optional[str]:
    """Return stripped text content of an XML element (if present)."""
    if elem is not None and elem.text is not None:
        return elem.text.strip()
    return None


def parse_drug_element(drug: ET.Element, ns: Dict[str, str]) -> Dict[str, object]:
    """Extract selected fields from a <drug> element.

    Parameters
    ----------
    drug : ET.Element
        The <drug> element to parse.
    ns : Dict[str, str]
        Namespace mapping for XML parsing.

    Returns
    -------
    Dict[str, object]
        A dictionary containing the filtered drug information.
    """
    data: Dict[str, object] = {}

    # Basic fields
    data["name"] = extract_text(drug.find("d:name", ns))
    data["description"] = extract_text(drug.find("d:description", ns))
    data["mechanism_of_action"] = extract_text(drug.find("d:mechanism-of-action", ns))
    data["pharmacodynamics"] = extract_text(drug.find("d:pharmacodynamics", ns))
    data["indication"] = extract_text(drug.find("d:indication", ns))

    # Toxicity information
    data["toxicity"] = extract_text(drug.find("d:toxicity", ns))

    # Classification: gather subfields if present
    classification: Dict[str, Optional[str]] = {}
    classification_elem = drug.find("d:classification", ns)
    if classification_elem is not None:
        for tag_name in [
            "description",
            "direct-parent",
            "kingdom",
            "superclass",
            "class",
            "subclass",
        ]:
            child = classification_elem.find(f"d:{tag_name}", ns)
            classification[tag_name.replace("-", "_")] = extract_text(child)
    data["classification"] = classification if classification else None

    # Affected organisms (list of strings)
    organisms_elem = drug.find("d:affected-organisms", ns)
    affected: List[str] = []
    if organisms_elem is not None:
        for ao in organisms_elem.findall("d:affected-organism", ns):
            text = extract_text(ao)
            if text:
                affected.append(text)
    data["affected_organisms"] = affected

    # We no longer extract drug interactions

    return data


def filter_drugbank_xml(input_path: str, output_path: str) -> None:
    """Parse the DrugBank XML and write filtered data to JSONL.

    Parameters
    ----------
    input_path : str
        Path to the original DrugBank XML file.
    output_path : str
        Path to the JSONL file to write filtered results.
    """
    # Namespace used in DrugBank XML
    ns = {"d": "http://www.drugbank.ca"}

    # Open output file
    with open(output_path, "w", encoding="utf-8") as outfile:
        # Use iterparse to process each <drug> element incrementally
        context = ET.iterparse(input_path, events=("end",))
        for event, elem in context:
            # Identify <drug> elements by local name (ignore namespace)
            if elem.tag.endswith("drug"):
                drug_data = parse_drug_element(elem, ns)
                outfile.write(json.dumps(drug_data, ensure_ascii=False) + "\n")
                # Clear the processed element from memory
                elem.clear()


def main() -> None:
    parser = argparse.ArgumentParser(description="Filter DrugBank XML fields")
    parser.add_argument("--input", required=True, help="Path to DrugBank XML file")
    parser.add_argument(
        "--output",
        required=True,
        help="Path to output JSONL file with filtered fields",
    )
    args = parser.parse_args()
    filter_drugbank_xml(args.input, args.output)


if __name__ == "__main__":
    main()

# 사용예시
#python "의약품데이터/drugbank_data/filter_drugbank_modified.py" --input "의약품데이터/drugbank_data/atc_split/atc_N.xml" --output "문항생성/atc_N_filtered.jsonl"
