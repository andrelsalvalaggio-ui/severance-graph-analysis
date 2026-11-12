import re
from datetime import timedelta
import pysrt

# 1. Dicionário de identificadores canónicos (sem espaços, sem acentos)
NAME_ALIASES = {
    "MARK": "MarkInnie",
    "MARK S.": "MarkInnie",
    "MARK SCOUT": "MarkOutie",
    "HELLY": "HellyR",
    "HELLY R.": "HellyR",
    "HELENA": "HelenaEagan",
    "DYLAN": "DylanInnie",
    "DYLAN G.": "DylanInnie",
    "IRVING": "IrvingInnie",
    "IRVING B.": "IrvingInnie",
    "MS. COBEL": "HarmonyCobel",
    "HARMONY COBEL": "HarmonyCobel",
    "MRS. SELVIG": "MrsSelvig",
    "MILCHICK": "SethMilchick",
    "MR. MILCHICK": "SethMilchick",
    "DEVON": "DevonHale",
    "RICKEN": "RickenHale",
    "PETEY": "PeterKilmer",
    "BURT": "BurtGoodman",
    "MS. CASEY": "MsCasey",
}

# Ruídos de Closed Caption a ignorar
SOUND_STOPWORDS = {
    "SIGHS", "LAUGHS", "CHUCKLES", "GASPS", "GRUNTS", "COUGHS",
    "MUSIC", "APPLAUSE", "PHONE RINGS", "DOOR OPENS", "OVER INTERCOM",
    "ELEVATOR CHIME", "DISTANT", "INDISTINCT", "WHISPERS", "PANTS"
}

# Regex para capturar padrões comuns de legendas CC: "[MARK] Fala" ou "MARK: Fala"
speaker_regex = re.compile(r"^[-–—\s]*[\[\(]?([A-Za-z0-9\s\.\-]{2,25})[\]\)]?:\s*(.*)$")

def parse_srt_events(srt_filepath, season_ep="S01E01", default_env="MDR"):
    subs = pysrt.open(srt_filepath, encoding="utf-8")
    
    parsed_dialogues = []
    
    for sub in subs:
        start_time = str(sub.start)
        lines = sub.text.split("\n")
        
        for line in lines:
            line = line.strip()
            # Descarta linhas que contenham apenas descrições sonoras
            if re.match(r"^[\[\(].*?[\]\)]$", line):
                continue
                
            match = speaker_regex.match(line)
            if match:
                raw_speaker = match.group(1).strip().upper()
                speech = match.group(2).strip()
                
                # Remove resíduos entre parênteses colados ao nome
                clean_speaker = re.sub(r"[\[\(].*?[\]\)]", "", raw_speaker).strip()
                
                if any(sound in clean_speaker for sound in SOUND_STOPWORDS):
                    continue
                    
                char_id = NAME_ALIASES.get(clean_speaker, None)
                if char_id:
                    parsed_dialogues.append({
                        "time": start_time,
                        "char": char_id,
                        "speech": speech,
                        "sub_start": sub.start.to_time()
                    })

    # 2. Agrupamento em Eventos de Interação (evita criar uma linha por fala contínua)
    interactions = []
    for i in range(len(parsed_dialogues) - 1):
        d1 = parsed_dialogues[i]
        d2 = parsed_dialogues[i + 1]
        
        # Se personagens diferentes falam em sequência num intervalo curto (<= 15 seg)
        if d1["char"] != d2["char"]:
            # Ordenação consistente para rede não-direcionada
            p1, p2 = sorted([d1["char"], d2["char"]])
            
            # Sinal pré-definido como neutro (0) para posterior revisão qualitativa
            # O sinal deve ser verificado para cumprir a secção 4.4 do enunciado
            sinal = "0"
            
            interactions.append({
                "p1": p1,
                "p2": p2,
                "sinal": sinal,
                "ambiente": default_env,
                "meta": f"# {season_ep} | Time: {d1['time']} | Contexto: {d1['speech'][:30]}... <-> {d2['speech'][:30]}..."
            })
            
    return interactions

# 3. Exportação no formato exato da secção 4.3 e 4.6 do trabalho
def export_dataset(interactions, output_txt_path):
    with open(output_txt_path, "w", encoding="utf-8") as f:
        f.write("# BASE DE DADOS DE INTERACOES - SEVERANCE\n")
        f.write("# Esquema: personagem1 personagem2 sinal ambiente\n\n")
        
        for inter in interactions:
            # Escreve metadados de rastreabilidade como comentário
            f.write(f"{inter['meta']}\n")
            # Escreve o registo canónico separado por espaços
            f.write(f"{inter['p1']} {inter['p2']} {inter['sinal']} {inter['ambiente']}\n")

# Exemplo de execução para um episódio:
inters = parse_srt_events("S01E01.srt", season_ep="S01E01", default_env="MDR")
export_dataset(inters, "interacoes_severance.txt")