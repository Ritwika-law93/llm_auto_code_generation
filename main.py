"""CLI entrypoint: runs the pipeline with the default PRD and stack."""
import logging

from generator import generate_all, write_documentation
from prompts import DEFAULT_STACK, PRD

# Configure logging for the CLI — INFO level shows pipeline progress without debug noise.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Starting CLI pipeline — stack=%r", DEFAULT_STACK)
    artifacts = generate_all(prd=PRD, stack=DEFAULT_STACK, on_step=print)
    write_documentation(artifacts)
    logger.info("Done. Output written to output_documentation.txt")


if __name__ == "__main__":
    main()
