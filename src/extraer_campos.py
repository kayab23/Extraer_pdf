from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "PEDIMENTOS 2025" / "PEDIMENTOS_VALIDOS"
OUT_JSON = ROOT / "salida" / "pedimentos_extraccion_campos.json"
OUT_CSV = ROOT / "salida" / "pedimentos_extraccion_campos.csv"

RFC_RE = re.compile(r"[A-ZÑ&]{3,4}[0-9]{6}[A-Z0-9]{3}", re.I)
NUM_RE = re.compile(r"\b\d{4,15}\b")
VAL_DOLARES_RE = re.compile(r"\$\s*[0-9\,]+(?:\.[0-9]{2})?")
PARTIDA_RE = re.compile(r"\b\d{2,6}\b")
FRACCION_RE = re.compile(r"\b\d{4,10}\b")
TASA_RE = re.compile(r"\b(?:[0-9]{1,2}(?:\.[0-9]+)?|0?\.[0-9]+)%\b")


def text_lines_from_pdf(path: Path) -> List[str]:
    out: List[str] = []
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t = page.extract_text() or ""
                lines = [l.strip() for l in t.splitlines() if l.strip()]
                out.extend(lines)
    except Exception:
        pass
    return out


def find_after_label(lines: List[str], keywords: List[str], look_next: int = 2) -> Optional[str]:
    for i, line in enumerate(lines):
        up = line.upper()
        for kw in keywords:
            if kw in up:
                # if colon present, return rest
                if ":" in line:
                    return line.split(":", 1)[1].strip()
                # else take same line after keyword
                idx = up.find(kw) + len(kw)
                tail = line[idx:].strip(" :.-\t")
                if tail:
                    return tail
                # else try next few lines
                for j in range(1, look_next + 1):
                    if i + j < len(lines):
                        candidate = lines[i + j].strip()
                        if candidate:
                            return candidate
    return None


def find_regex_in_lines(lines: List[str], regex: re.Pattern) -> Optional[str]:
    for line in lines:
        m = regex.search(line)
        if m:
            return m.group(0)
    return None


def extract_fields_from_file(path: Path) -> Dict[str, Any]:
    lines = text_lines_from_pdf(path)
    up = "\n".join(lines)

    res: Dict[str, Any] = {"file": path.name}

    # NUM. PEDIMENTO
    num_ped = find_after_label(lines, ["NUM PEDIMENTO", "NUM. PEDIMENTO", "PEDIMENTO", "NO. PEDIMENTO", "NÚM PEDIMENTO"]) or find_regex_in_lines(lines, NUM_RE)
    res["NUM. PEDIMENTO"] = num_ped or ""

    # ADUANA E/S
    aduana = find_after_label(lines, ["ADUANA E/S", "ADUANA", "E/S"]) or ""
    res["ADUANA E/S"] = aduana

    # ID. FISCAL - try RFC or numeric id
    id_fiscal = find_after_label(lines, ["ID FISCAL", "ID. FISCAL", "ID FISCA", "RFC"]) or find_regex_in_lines(lines, RFC_RE) or find_regex_in_lines(lines, NUM_RE)
    res["ID. FISCAL"] = id_fiscal or ""

    # NOMBRE / DENOMINACION O RAZON SOCIAL
    nombre = find_after_label(lines, ["NOMBRE, DENOMINACION", "NOMBRE", "DENOMINACION", "RAZON SOCIAL", "NOMBRE O RAZON SOCIAL"]) or ""
    res["NOMBRE, DENOMINACION O RAZON SOCIAL DEL PROVEEDOR"] = nombre

    # VAL. DOLARES
    val_dol = find_after_label(lines, ["VAL. DOLARES", "VAL DOLARES", "VALOR DOLARES", "VALOR EN DOLARES"]) or find_regex_in_lines(lines, VAL_DOLARES_RE)
    res["VAL. DOLARES"] = val_dol or ""

    # PARTIDA (SEC)
    partida = find_after_label(lines, ["PARTIDA", "PARTIDA (SEC)", "PARTIDA (SEC)"]) or find_regex_in_lines(lines, PARTIDA_RE)
    res["PARTIDA (SEC)"] = partida or ""

    # FRACCION
    fraccion = find_after_label(lines, ["FRACCION", "FRACCIÓN"]) or find_regex_in_lines(lines, FRACCION_RE)
    res["FRACCION"] = fraccion or ""

    # DESCRIPCION
    descripcion = find_after_label(lines, ["DESCRIPCION", "DESCRIPCIÓN", "DESCRIPCIÓN DE LA MERCANCÍA"]) or ""
    res["DESCRIPCION"] = descripcion

    # TASA DE IGI
    tasa = find_after_label(lines, ["TASA DE IGI", "TASA IGI", "TASA DE IGI %", "TASA DE IGI (% )"]) or find_regex_in_lines(lines, TASA_RE)
    res["TASA DE IGI"] = tasa or ""

    return res


def main() -> None:
    out: List[Dict[str, Any]] = []
    for p in sorted(PDF_DIR.rglob("*.pdf")):
        print("Procesando:", p.name)
        try:
            data = extract_fields_from_file(p)
            out.append(data)
        except Exception as e:
            out.append({"file": p.name, "error": str(e)})

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with OUT_JSON.open("w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)

    # CSV
    keys = ["file", "NUM. PEDIMENTO", "ADUANA E/S", "ID. FISCAL", "NOMBRE, DENOMINACION O RAZON SOCIAL DEL PROVEEDOR", "VAL. DOLARES", "PARTIDA (SEC)", "FRACCION", "DESCRIPCION", "TASA DE IGI"]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(keys)
        for row in out:
            writer.writerow([row.get(k, "") for k in keys])

    print("Extracción completada. Archivos:")
    print(OUT_JSON)
    print(OUT_CSV)


if __name__ == "__main__":
    main()
