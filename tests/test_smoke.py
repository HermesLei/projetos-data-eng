import csv

import pytest

from pipelines.load_customers import read_customers


def test_read_valid_customers():
    customers = read_customers()

    assert len(customers) == 5
    assert customers[0] == {
        "customer_id": 1,
        "name": "Ana Souza",
        "city": "Sao Paulo",
    }


def test_rejects_invalid_header(tmp_path):
    csv_path = tmp_path / "customers.csv"
    csv_path.write_text("id,name,city\n1,Ana,Sao Paulo\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Cabeçalho inválido"):
        read_customers(csv_path)


def test_rejects_empty_required_field(tmp_path):
    csv_path = tmp_path / "customers.csv"
    csv_path.write_text(
        "customer_id,name,city\n1,,Sao Paulo\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Campo obrigatório vazio"):
        read_customers(csv_path)


def test_rejects_duplicate_customer_ids(tmp_path):
    csv_path = tmp_path / "customers.csv"

    with csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["customer_id", "name", "city"],
        )
        writer.writeheader()
        writer.writerow(
            {"customer_id": 1, "name": "Ana", "city": "Sao Paulo"}
        )
        writer.writerow(
            {"customer_id": 1, "name": "Bruno", "city": "Curitiba"}
        )

    with pytest.raises(ValueError, match="customer_id duplicado"):
        read_customers(csv_path)
