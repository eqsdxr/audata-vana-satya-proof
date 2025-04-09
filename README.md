Project structure:

- `my_proof/`: Contains the main proof logic
  - `proof.py`: Implements the proof generation logic
  - `__main__.py`: Entry point for the proof execution
  - `handlers.py`: Implements parameter evaluators
  - `db.py`: Contains db logic
  - `utils.py`: Project's utils
  - `config.py`: Configuration file
  - `models/`
    - `db.py`: Database orm models
    - `proof-response.py`: Implements pydantic model of proof response
- `demo/`: Contains sample input and output for testing
- `.github/workflows/`: CI/CD pipeline for building and releasing
- `Dockerfile`: Defines the container image for the proof task
- `my-proof.manifest.template`: Gramine manifest template for running securely in an Intel SGX enclave
- `config.yaml`: Configuration file for Gramine Shielded Containers (GSC)

To run the proof locally:

```
docker build -t audata-proof .
docker run \
--rm \
--volume $(pwd)/demo/sealed:/sealed \
--volume $(pwd)/demo/input:/input \
--volume $(pwd)/demo/output:/output \
audata-proof
```

Remember to populate the `/input` directory with the files you want to process.
