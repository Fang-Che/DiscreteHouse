# DiscreteHouse
## WikiHouse AI-Assisted Design-Manufacture-Assembly Platform

A research platform that integrates Large Language Models (LLMs) with a 
Fabrication-Aware Discrete Design Grammar to generate structurally valid 
and manufacturable WikiHouse Skylark configurations from natural language input.

---

## Research Context

**PhD Research** | Architecture | Design-to-Build AI Workflow  
**Core Contribution**: Fabrication-Aware Discrete Design Grammar (FADDG)  
**System**: WikiHouse Skylark (SK200 + SK250)  
**License**: Creative Commons Attribution-ShareAlike 4.0

---

## System Overview

---

## Features

- **Natural Language Design Input**: Describe your space needs in Chinese or English
- **198 Official WikiHouse Blocks**: Complete SK250 and SK200 block library
- **Fabrication-Aware Validation**: 10-layer grammar based on official WikiHouse design guides
- **Official 3D Isometric Views**: ISO SVG images directly from WikiHouse GitHub
- **CNC Cutting Layouts**: Direct links to official DXF cutting files
- **Assembly Sequence Generation**: Automatically generates step-by-step assembly order

---

## Installation

### Prerequisites
- Python 3.10+
- Anthropic API Key ([Get one here](https://console.anthropic.com))

### Setup

```bash
# Clone repository
git clone https://github.com/Fang-Che/DiscreteHouse.git
cd DiscreteHouse

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install streamlit anthropic python-dotenv beautifulsoup4 matplotlib

# Set up API key
echo "ANTHROPIC_API_KEY=your_key_here" > .env

# Run the app
streamlit run app.py
```

---

## Data

The block library (`data/blocks_full.json`) contains 198 official WikiHouse 
Skylark blocks, scraped from wikihouse.cc, including:
- Block dimensions (w/l/h in mm)
- Materials (OSB3 sheets, fixings, insulation)
- Cost, weight, carbon data
- ISO isometric SVG image URLs
- CNC cutting file links (DXF)
- Parts list for each block

To refresh the data:
```bash
python fetch_blocks_full.py
```

---

## Grammar Structure

The Connection Grammar (`utils/connection_grammar.py`) encodes WikiHouse's 
fabrication constraints across 10 layers:

1. Material & Fabrication Constraints
2. Geometric Constraints  
3. Structural Constraints (lateral bracing rules)
4. Roof Type Rules
5. Block Category Mapping
6. Connection Rules (face-to-face compatibility)
7. Height Compatibility Rules
8. Span Compatibility Rules
9. Assembly Sequence Constraints
10. Forbidden Combinations (7 hard rules)

All rules are sourced from official WikiHouse Design Guides.

---

## Official Sources

- [WikiHouse Design Guide](https://www.wikihouse.cc/design/designing-for-wikihouse)
- [How the Structure Works](https://www.wikihouse.cc/design/how-the-structure-works)
- [WikiHouse Block Library](https://www.wikihouse.cc/blocks/skylark-250)
- [WikiHouse GitHub](https://github.com/wikihouseproject/Skylark)

---

## Research References

- Rossi, A. & Tessmann, O. (2017). Wasp: Discrete Design with Grasshopper. DDU, TU Darmstadt.
- Luo, J. et al. (2024). Voxel-based Modular Architectural Design Strategy. BioResources, 19(3).
- Küpfer, C. et al. (2024). Advancing Sustainable Construction: Discrete Modular Systems. MDPI Sustainability.

---

## License

This project is for academic research purposes.  
WikiHouse Skylark files are licensed under [Creative Commons Attribution-ShareAlike 4.0](https://creativecommons.org/licenses/by-sa/4.0/).

---

## Author

Fang-Che | PhD Candidate | Architecture  
GitHub: [@Fang-Che](https://github.com/Fang-Che)