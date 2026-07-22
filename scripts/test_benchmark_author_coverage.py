import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("benchmark_author_coverage.py")
SPEC = importlib.util.spec_from_file_location("benchmark_author_coverage", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


assert MODULE.name_equivalent("Li Fei-Fei", "Fei-Fei Li")
assert MODULE.name_equivalent("Ming-Hsuan Yang", "Ming Hsuan Yang")
assert not MODULE.name_equivalent("Lei Zhang", "Li Zhang")
assert not MODULE.name_equivalent("James Hays", "James Hayes")

print("OK benchmark author-name equivalence")
