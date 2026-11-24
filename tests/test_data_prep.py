import pandas as pd
from data_prep import prepare, public_data

def test_forwardfill_and_missing():
    df = prepare(pd.DataFrame([{"Institution":"UFS", "Module code":"A", "Discipline":"Aplied: Biostatistics", "Information provider":"private"}, {"Institution":None, "Module code":"B", "Discipline":"?"}]))
    assert df.loc[1,"Institution"] == "UFS"
    assert df.loc[0,"Discipline display"] == "Applied: Biostatistics"
    assert "Information provider" not in public_data(df).columns
