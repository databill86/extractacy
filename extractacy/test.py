import pytest
import spacy
from spacy.pipeline import EntityRuler
from extract import ValueExtractor


def build_docs():
    docs = list()
    docs.append(
        (
            "Discharge Date: 11/15/2008. Patient had temp reading of 102.6 degrees. Insurance claim sent to patient's account on file: 1112223. 12/31/2008: Payment received.",
            [
                ("Discharge Date", ["11/15/2008"]),
                ("11/15/2008", []),
                ("temp", ["102.6 degrees"]),
                ("102.6 degrees", []),
                ("account", ["1112223"]),
                ("1112223", []),
                # ("12/31/2008", []),
                ("Payment received", ["12/31/2008"]),
            ],
        )
    )
    # testing a case where algorithm attempts to go left of a document start boundary
    docs.append(("Payment update: Funds deposited.", [("Payment update", []),],))
    # testing a case where algorithm attempts to go right of a document end boundary
    docs.append(("We do not know the discharge date", [("discharge date", []),],))
    docs.append((":Payment update: Funds deposited.", [("Payment update", []),],))
    docs.append(("We do not know the discharge date.", [("discharge date", []),],))
    # check "both" direction with "sent"
    docs.append(
        (
            "We believe 01/01/1980 is his date of birth but it could also be 01/02/1980",
            [("date of birth", ["01/01/1980", "01/02/1980"]),],
        )
    )
    docs.append(
        (
            "Birthdate: 01/01/1980.",
            [("Birthdate", ["01/01/1980"]), ("01/01/1980", []),],
        )
    )

    return docs


def test():
    nlp = spacy.load("en_core_web_sm")
    ruler = EntityRuler(nlp)
    patterns = [
        {"label": "TEMP_READING", "pattern": [{"LOWER": "temperature"}]},
        {"label": "TEMP_READING", "pattern": [{"LOWER": "temp"}]},
        {
            "label": "DISCHARGE_DATE",
            "pattern": [{"LOWER": "discharge"}, {"LOWER": "date"}],
        },
        {"label": "ACCOUNT", "pattern": [{"LOWER": "account"}]},
        {"label": "PAYMENT", "pattern": [{"LOWER": "payment"}, {"LOWER": "received"}]},
        {"label": "PAYMENT", "pattern": [{"LOWER": "payment"}, {"LOWER": "update"}]},
        {"label": "BIRTHDATE", "pattern": [{"LOWER": "birthdate"}]},
        {
            "label": "BIRTHDATE",
            "pattern": [{"LOWER": "date"}, {"LOWER": "of"}, {"LOWER": "birth"}],
        },
    ]
    ruler.add_patterns(patterns)
    nlp.add_pipe(ruler, last=True)

    ent_patterns = {
        "DISCHARGE_DATE": {
            "patterns": [[{"SHAPE": "dd/dd/dddd"}],[{"SHAPE": "dd/d/dddd"}]],
            "n": 2,
            "direction": "right",
        },
        "PAYMENT": {
            "patterns": [[{"SHAPE": "dd/dd/dddd"}]],
            "n": 2,
            "direction": "left",
        },
        "TEMP_READING": {
            "patterns": [
                [
                    {"LIKE_NUM": True},
                    {
                        "LOWER": {
                            "IN": [
                                "f",
                                "c",
                                "farenheit",
                                "celcius",
                                "centigrade",
                                "degrees",
                            ]
                        }
                    },
                ]
            ],
            "n": 7,
            "direction": "right",
        },
        "ACCOUNT": {
            "patterns": [[{"LIKE_NUM": True, "LENGTH": {"==": 7}},]],
            "n": "sent",
            "direction": "right",
        },
        "BIRTHDATE": {
            "patterns": [[{"SHAPE": "dd/dd/dddd"}]],
            "n": "sent",
            "direction": "both",
        },
    }

    valext = ValueExtractor(nlp, ent_patterns)
    nlp.add_pipe(valext, last=True)
    docs = build_docs()
    for d in docs:
        doc = nlp(d[0])
        for i, e in enumerate(doc.ents):
            print(e.text, e._.value_extract)
            assert (e.text, e._.value_extract) == d[1][i]


if __name__ == "__main__":
    test()
