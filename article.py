import requests
import time
import random
from pyvis.network import Network

HEADERS = {"User-Agent": "CitationGraphBot/1.0"}
OPENALEX_API = "https://api.openalex.org/works/"
MAX_CITED_BY = 20  # Limite de citations inverses


def resolve_id(identifier):
    if identifier.startswith("https://openalex.org/"):
        identifier = identifier.split("/")[-1]
    if identifier.startswith("W"):
        url = OPENALEX_API + identifier
    else:
        url = OPENALEX_API + "https://doi.org/" + identifier

    try:
        r = requests.get(url, headers=HEADERS)
        if r.status_code != 200 or not r.content or r.text.strip() == "":
            print(f"⚠Réponse vide pour {identifier}")
            return None
        data = r.json()
        return {
            "id": data["id"].split("/")[-1],
            "title": data.get("display_name", "Unknown"),
            "year": str(data.get("publication_year", "???")),
            "references": [ref.split("/")[-1] for ref in data.get("referenced_works", [])]
        }
    except Exception as e:
        print(f"💥 Erreur sur {identifier}: {e}")
        return None

# === CITES: ===
def get_cited_by(openalex_id, max_results=MAX_CITED_BY):
    try:
        short_id = openalex_id.split("/")[-1]
        url = f"https://api.openalex.org/works?filter=cites:{short_id}&per-page={max_results}"
        r = requests.get(url, headers=HEADERS)
        r.raise_for_status()
        data = r.json()
        return [item["id"].split("/")[-1] for item in data.get("results", [])]
    except Exception as e:
        print(f"⚠️ Erreur sur get_cited_by({openalex_id}): {e}")
        return []

# === COULEUR ALÉATOIRE PAR NIVEAU ===
level_colors = {}

def get_color_for_level(level):
    if level not in level_colors:
        level_colors[level] = "#{:06x}".format(random.randint(0, 0xFFFFFF))
    return level_colors[level]

# === GRAPHE PYVIS ===
def build_graph(starting_dois, depth=2, delay=0.2,limit=-1, include_cited_by=True):
    net = Network(height="800px", width="100%", directed=True)
    visited_nodes = set()
    titles_cache = {}

    def get_or_resolve_title(openalex_id):
        if openalex_id in titles_cache:
            return titles_cache[openalex_id]
        ref_data = resolve_id(openalex_id)
        if ref_data:
            titles_cache[openalex_id] = ref_data["title"]
            return ref_data["title"]
        return openalex_id  # fallback

    def recurse(ids, level):
        i = 0
        print(f"\n Niveau {level} : {len(ids)} nœuds à traiter")
        if level > depth:
            return

        ids = [i.split("/")[-1] if i.startswith("http") else i for i in ids]
        next_ids = []

        for ident in ids:
            if ident in visited_nodes:
                continue

            work = resolve_id(ident)
            if not work:
                continue

            node_id = work["id"]
            title = work["title"]
            titles_cache[node_id] = title
            visited_nodes.add(node_id)

            color = get_color_for_level(level)
            net.add_node(node_id, label=title, title=f"{title} ({work['year']})", color=color)
            a = len(visited_nodes)

            # ➤ Références (sortantes)
            for ref in work["references"]:

                if(a + i > limit and limit > 1 ):
                    return net
                #print(ref)
                ref_title = get_or_resolve_title(ref)
                net.add_node(ref, label=ref_title, title=ref_title, color=get_color_for_level(level + 1))
                net.add_edge(node_id, ref)
                if ref not in visited_nodes:
                    i=i+1
                    next_ids.append(ref)
            time.sleep(delay)

        recurse(next_ids, level + 1)

    recurse(starting_dois, 1)
    return net

# === ARTICLES DE DÉPART ===
starting_dois = [
    #"10.1007/3-540-61794-9_52",
    #"10.3906/elk-1909-14",
    #"10.1016/j.eswa.2021.115363",
    # "10.1007/s10287-007-0066-8",
    # "10.1016/S0377-2217(00)00052-7",
    # "10.1007/s10951-009-0153-5",
    # "10.1016/j.techfore.2024.123687",
    # "10.1016/j.sbspro.2011.05.087",
     #"10.1007/3-540-61794-9_49",
    "10.1609/socs.v4i1.18291"
]

# === LANCEMENT ===
graph = build_graph(starting_dois, depth=1, limit=4000,delay=0 , include_cited_by=False)
graph.write_html("citation_graph_colored.html")