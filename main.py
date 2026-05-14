"""CLI entrypoint: runs the pipeline with the default PRD and stack."""
from generator import generate_all, write_documentation
from prompts import DEFAULT_STACK, PRD


def main() -> None:
    artifacts = generate_all(prd=PRD, stack=DEFAULT_STACK, on_step=print)
    write_documentation(artifacts)
    print("Wrote output_documentation.txt")


if __name__ == "__main__":
    main()
