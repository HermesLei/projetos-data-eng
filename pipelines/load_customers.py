import csv
import os
from pathlib import Path

from sqlalchemy import (
    Integer,
    String,
    create_engine,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

ROOT_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT_DIR / "data" / "samples" / "customers.csv"


class Base(DeclarativeBase):
    pass


class Customer(Base):
    __tablename__ = "customers"

    customer_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)


def read_customers(
    csv_path: Path = CSV_PATH,
) -> list[dict[str, object]]:
    customers: list[dict[str, object]] = []

    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        expected_columns = ["customer_id", "name", "city"]

        if reader.fieldnames != expected_columns:
            raise ValueError(
                f"Cabeçalho inválido. Esperado: {expected_columns}"
            )

        for line_number, row in enumerate(reader, start=2):
            if not row["customer_id"] or not row["name"] or not row["city"]:
                raise ValueError(
                    f"Campo obrigatório vazio na linha {line_number}."
                )

            try:
                customer_id = int(row["customer_id"])
            except ValueError as exc:
                raise ValueError(
                    f"customer_id inválido na linha {line_number}."
                ) from exc

            if customer_id <= 0:
                raise ValueError(
                    f"customer_id deve ser positivo na linha {line_number}."
                )

            customers.append(
                {
                    "customer_id": customer_id,
                    "name": row["name"].strip(),
                    "city": row["city"].strip(),
                }
            )

    if not customers:
        raise ValueError("O CSV não contém clientes.")

    ids = [customer["customer_id"] for customer in customers]
    if len(ids) != len(set(ids)):
        raise ValueError("O CSV contém customer_id duplicado.")

    return customers


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("A variável DATABASE_URL não foi definida.")

    customers = read_customers()
    engine = create_engine(database_url)

    try:
        Base.metadata.create_all(engine)

        with engine.begin() as connection:
            connection.execute(
                text("DELETE FROM customers")
            )
            connection.execute(
                text(
                    """
                    INSERT INTO customers (customer_id, name, city)
                    VALUES (:customer_id, :name, :city)
                    """
                ),
                customers,
            )

            total = connection.execute(
                text("SELECT COUNT(*) FROM customers")
            ).scalar_one()

        print(f"Pipeline concluído: {total} clientes carregados.")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
