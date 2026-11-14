"""Script tạo file benchmark riêng biệt cho Thử thách nâng cao (ADVANCED.md).
Gồm:
- Dev (18 câu): 15 có đáp án + 3 thiếu bằng chứng.
- Test (30 câu): Đúng 6 nhóm (Bảng 6, Ảnh 5, Biểu đồ 5, Multi-hop 4, Text 4, Thiếu bằng chứng 6).
Tổng cộng: 48 câu.
"""
import json
import re
from pathlib import Path


def main():
    chunks = json.loads(Path("data/chunks.json").read_text(encoding="utf-8"))

    # 1. TẬP DEV: 15 câu có đáp án + 3 câu thiếu bằng chứng = 18 câu
    day6 = json.loads(Path("D:/LAB AI/lab06/K5-L3A-DAY06-2A202603617-DataIngestion/data/benchmark.json").read_text(encoding="utf-8"))
    dev_questions = []
    for q in day6["questions"]:
        if q["split"] != "dev":
            continue
        ev = q["evidence_quote"]
        exact_ev = ev
        for c in chunks:
            if c["source_id"] == q["gold_source_id"] and c["page"] == q["gold_page"]:
                m = re.search(r"\s+".join(re.escape(w) for w in ev.split()), c["text"])
                if m:
                    exact_ev = m.group(0)
                    break
        dev_questions.append({
            "id": q["id"],
            "split": "dev",
            "group": "text",
            "question": q["question"],
            "expected_answer": q["expected_answer"],
            "gold": [{"source_id": q["gold_source_id"], "page": q["gold_page"], "evidence": exact_ev}],
            "filter": q.get("filter")
        })

    # 3 câu thiếu bằng chứng cho dev
    dev_unans = [
        {"id": "adv_unans_dev_01", "split": "dev", "group": "abstention", "question": "What are the safety guidelines for growing commercial seaweeds in hydroponic chambers on Mars?", "expected_answer": "Không đủ bằng chứng để trả lời.", "gold": []},
        {"id": "adv_unans_dev_02", "split": "dev", "group": "abstention", "question": "What are the European Union regulations regarding seaweed aquaculture licensing enacted in the year 2026?", "expected_answer": "Không đủ bằng chứng để trả lời.", "gold": []},
        {"id": "adv_unans_dev_03", "split": "dev", "group": "abstention", "question": "Which cryptocurrency or blockchain network is used by the FAO to verify organic seaweed export certificates?", "expected_answer": "Không đủ bằng chứng để trả lời.", "gold": []}
    ]
    dev_questions.extend(dev_unans)

    # 2. TẬP TEST NÂNG CAO: Đúng 30 câu chia 6 nhóm theo ADVANCED.md
    test_questions = [
        # NHÓM 1: BẢNG SỐ LIỆU (6 CÂU)
        {
            "id": "adv_test_tbl_01", "split": "test", "group": "table",
            "question": "In Chapter 2 (Table 1 and Section 2.6 on quantities harvested), which country was the largest supplier of Gracilaria in 2000, and what was its harvested quantity in wet tonnes?",
            "expected_answer": "Chile was the largest supplier of Gracilaria in 2000, harvesting 137 000 wet tonnes.",
            "gold": [{"source_id": "fao_seaweed_guide", "page": 27, "evidence": "For Gracilaria, Chile is the largest supplier, although the harvest\nof wild seaweed has fluctuated over the last 5 years, from 121 000\nwet tonnes in 1996 down to 73 000 tonnes in 1998, and back up\nto 137 000 wet tonnes in 2000."}]
        },
        {
            "id": "adv_test_tbl_02", "split": "test", "group": "table",
            "question": "According to Table 2 in Chapter 3, what is the agar processing capacity of the Americas in tonnes?",
            "expected_answer": "3 000 tonnes (accounting for 39 percent of global capacity).",
            "gold": [{"source_id": "fao_seaweed_guide", "page": 34, "evidence": "Americas\n3 000\n39 percent\nTotal 7 630\nTable 2\nAgar processors."}]
        },
        {
            "id": "adv_test_tbl_03", "split": "test", "group": "table",
            "question": "According to Table 3, which application represents the largest volume market for agar and what is its annual tonnage?",
            "expected_answer": "Food application (specifically bakers and confectioners), with an annual volume of approximately 6 930 tonnes (91%).",
            "gold": [{"source_id": "fao_seaweed_guide", "page": 37, "evidence": "TABLE 3\nAgar markets (2001)"}]
        },
        {
            "id": "adv_test_tbl_04", "split": "test", "group": "table",
            "question": "What is the total annual market value of all agar markets combined as summarized in Table 3?",
            "expected_answer": "US$ 137 million.",
            "gold": [{"source_id": "fao_seaweed_guide", "page": 37, "evidence": "US$ 137 million."}]
        },
        {
            "id": "adv_test_tbl_05", "split": "test", "group": "table",
            "question": "According to Chapter 4 (Section 4.5 and Section 4.6), what brown seaweed species cultivated in China for food is sometimes diverted to the alginate industry?",
            "expected_answer": "Laminaria japonica.",
            "gold": [{"source_id": "fao_seaweed_guide", "page": 48, "evidence": "The only exception is for Laminaria japonica, which is cultivated in China\nfor food but sometimes surplus material is diverted to the alginate industry in China."}]
        },
        {
            "id": "adv_test_tbl_06", "split": "test", "group": "table",
            "question": "According to Section 5.5 and Table 6 in Chapter 5, what application accounts for about half of the global market for alginates?",
            "expected_answer": "Textile printing applications, accounting for about half (50%) of the global alginate market.",
            "gold": [{"source_id": "fao_seaweed_guide", "page": 61, "evidence": "textile printing applications\naccounting for about half of the global market"}]
        },

        # NHÓM 2: ẢNH CHỤP & THIẾT BỊ (5 CÂU)
        {
            "id": "adv_test_fig_01", "split": "test", "group": "figure",
            "question": "In Chapter 2, which two genera of agarophytes are illustrated in Figure 1 and Figure 2 respectively?",
            "expected_answer": "Gelidium is shown in Figure 1 and Gracilaria is shown in Figure 2.",
            "gold": [{"source_id": "fao_seaweed_guide", "page": 21, "evidence": "Most agar is extracted from species of Gelidium (Figure 1) and Gracilaria (Figure 2)."}]
        },
        {
            "id": "adv_test_fig_02", "split": "test", "group": "figure",
            "question": "According to the caption of Figure 4, where is the illustrated pond used for Gracilaria cultivation located?",
            "expected_answer": "In Sulawesi, Indonesia.",
            "gold": [{"source_id": "fao_seaweed_guide", "page": 25, "evidence": "FIGURE 4\nPond used for\nGracilaria cultivation,\nSulawesi, Indonesia."}]
        },
        {
            "id": "adv_test_fig_03", "split": "test", "group": "figure",
            "question": "What process is illustrated in Figure 9 during agar extraction in Chapter 3?",
            "expected_answer": "Thawing frozen slabs of agar by hosing with water.",
            "gold": [{"source_id": "fao_seaweed_guide", "page": 31, "evidence": "FIGURE 9\nThawing frozen slabs of agar by\nhosing with water."}]
        },
        {
            "id": "adv_test_fig_04", "split": "test", "group": "figure",
            "question": "What is the function of the industrial equipment shown in Figure 10 in agar production?",
            "expected_answer": "It is a dewatering machine used to squeeze water from agar gel.",
            "gold": [{"source_id": "fao_seaweed_guide", "page": 31, "evidence": "FIGURE 10\nDewatering machine used to\nsqueeze water from agar gel."}]
        },
        {
            "id": "adv_test_fig_05", "split": "test", "group": "figure",
            "question": "What two physical forms of commercial agar are illustrated in Figure 12?",
            "expected_answer": "Agar blocks (left) and agar strips (right).",
            "gold": [{"source_id": "fao_seaweed_guide", "page": 32, "evidence": "FIGURE 12\nAgar blocks (left) and agar strips\n(right)."}]
        },

        # NHÓM 3: BIỂU ĐỒ LƯU TRÌNH (5 CÂU)
        {
            "id": "adv_test_cht_01", "split": "test", "group": "chart",
            "question": "What process is charted in the flow chart shown in Figure 13 and which authors is it attributed to?",
            "expected_answer": "Flow chart for the production of agar, after Armisen and Galatas (1987).",
            "gold": [{"source_id": "fao_seaweed_guide", "page": 32, "evidence": "FIGURE 13\nFlow chart for the production of\nagar (after Armisen and Galatas,\n1987)."}]
        },
        {
            "id": "adv_test_cht_02", "split": "test", "group": "chart",
            "question": "In the agar production process described in Chapter 3, what must be done to the thick extract before cooling it to form a gel?",
            "expected_answer": "The extract must be kept hot during filtration.",
            "gold": [{"source_id": "fao_seaweed_guide", "page": 29, "evidence": "The extract is thick and will gel if allowed to cool, so it must be kept\nhot during the filtration processes."}]
        },
        {
            "id": "adv_test_cht_03", "split": "test", "group": "chart",
            "question": "What chemical is added to the seaweed slurry in the alginate flow chart to convert insoluble alginic acid into soluble sodium alginate?",
            "expected_answer": "Sodium carbonate (soda ash).",
            "gold": [{"source_id": "fao_seaweed_guide", "page": 50, "evidence": "Sodium carbonate (soda ash) is added"}]
        },
        {
            "id": "adv_test_cht_04", "split": "test", "group": "chart",
            "question": "In the alginate manufacturing process and flow chart (Figure 32), what two alternate precipitation routes can be used to separate alginate from clarified extract?",
            "expected_answer": "Precipitation as calcium alginate or precipitation as alginic acid.",
            "gold": [{"source_id": "fao_seaweed_guide", "page": 52, "evidence": "FIGURE 32\nFlow chart for the\nproduction of sodium\nalginate"}]
        },
        {
            "id": "adv_test_cht_05", "split": "test", "group": "chart",
            "question": "In Chapter 7 (Section 7.1.2 and Figure 46), what is the key characteristic feature of the semi-refined carrageenan (SRC) processing method?",
            "expected_answer": "In semi-refined carrageenan processing, the carrageenan is never actually extracted from the seaweed.",
            "gold": [{"source_id": "fao_seaweed_guide", "page": 75, "evidence": "This is the method in which the\ncarrageenan is never actually extracted from the seaweed."}]
        },

        # NHÓM 4: MULTI-HOP (4 CÂU)
        {
            "id": "adv_test_hop_01", "split": "test", "group": "multihop",
            "question": "What three hydrocolloids extracted from seaweeds are described in Chapter 1, and which seaweed species is the main source of agar in India according to Chapter 2?",
            "expected_answer": "The three hydrocolloids are agar, alginate, and carrageenan; Gelidiella acerosa is the main source of agar in India.",
            "gold": [
                {"source_id": "fao_seaweed_guide", "page": 14, "evidence": "Various red and brown seaweeds are used to produce three hydrocolloids: agar, alginate\nand carrageenan."},
                {"source_id": "fao_seaweed_guide", "page": 21, "evidence": "Gelidiella acerosa is the\nmain source of agar in India."}
            ]
        },
        {
            "id": "adv_test_hop_02", "split": "test", "group": "multihop",
            "question": "Why are species of Pterocladia collected according to Chapter 2, and in what two countries or territories are they mainly harvested?",
            "expected_answer": "They are collected as a source of agar, mainly in the Azores (Portugal) and New Zealand.",
            "gold": [{"source_id": "fao_seaweed_guide", "page": 21, "evidence": "Closely related to Gelidium are species of Pterocladia, and small quantities of these are\ncollected, mainly in the Azores (Portugal) and New Zealand."}]
        },
        {
            "id": "adv_test_hop_03", "split": "test", "group": "multihop",
            "question": "What percentage of raw agar gel consists of water before removal, and what mechanical machine shown in Figure 10 is used to squeeze it out?",
            "expected_answer": "Water constitutes about 99 percent of the raw gel, which can be squeezed out using a dewatering machine.",
            "gold": [
                {"source_id": "fao_seaweed_guide", "page": 29, "evidence": "The remaining 99 percent is water"},
                {"source_id": "fao_seaweed_guide", "page": 31, "evidence": "FIGURE 10\nDewatering machine used to\nsqueeze water from agar gel."}
            ]
        },
        {
            "id": "adv_test_hop_04", "split": "test", "group": "multihop",
            "question": "Why cannot potassium-based gel processing be used for lambda carrageenan in semi-refined carrageenan production according to Chapter 7?",
            "expected_answer": "Because lambda carrageenans do not form gels with potassium and would therefore dissolve and be lost during alkali treatment.",
            "gold": [
                {"source_id": "fao_seaweed_guide", "page": 76, "evidence": "Lambda carrageenans do not form gels with\npotassium and would therefore dissolve and be lost during the alkali treatment."}
            ]
        },

        # NHÓM 5: VĂN BẢN (TEXT) (4 CÂU)
        {
            "id": "adv_test_txt_01", "split": "test", "group": "text",
            "question": "What has caused a revival of interest in using seaweeds for agricultural fertilizers?",
            "expected_answer": "The rising popularity of organic farming.",
            "gold": [{"source_id": "fao_seaweed_guide", "page": 15, "evidence": "Today, with the rising popularity of organic farming, there has been some revival of the industry"}]
        },
        {
            "id": "adv_test_txt_02", "split": "test", "group": "text",
            "question": "In what zone does the brown seaweed Laminaria saccharina typically grow?",
            "expected_answer": "In the upper sublittoral zone.",
            "gold": [{"source_id": "fao_seaweed_guide", "page": 42, "evidence": "Laminaria saccharina also grows in the upper sublittoral"}]
        },
        {
            "id": "adv_test_txt_03", "split": "test", "group": "text",
            "question": "Which countries have a multi-century tradition of using seaweeds as direct human food?",
            "expected_answer": "China, Japan, and the Republic of Korea.",
            "gold": [{"source_id": "fao_seaweed_guide", "page": 85, "evidence": "For several centuries there has been a traditional use of seaweeds as food in China, Japan and the Republic of Korea."}]
        },
        {
            "id": "adv_test_txt_04", "split": "test", "group": "text",
            "question": "What is the nutritional value of Porphyra (nori) in terms of protein content and digestibility?",
            "expected_answer": "Porphyra has a protein content of 30–50 percent, and about 75 percent of that protein is digestible.",
            "gold": [{"source_id": "fao_seaweed_guide", "page": 86, "evidence": "It is among the most nutritious seaweeds, with a protein content of 30–50 percent, and about 75 percent of that is digestible."}]
        },

        # NHÓM 6: THIẾU BẰNG CHỨNG (ABSTENTION) (6 CÂU)
        {
            "id": "adv_test_abs_01", "split": "test", "group": "abstention",
            "question": "How is CRISPR-Cas9 genome editing specifically applied to improve the carrageenan yield in Kappaphycus alvarezii?",
            "expected_answer": "Không đủ bằng chứng để trả lời.", "gold": []
        },
        {
            "id": "adv_test_abs_02", "split": "test", "group": "abstention",
            "question": "What is the market share of sodium alginate used as an electrolyte binder in lithium-ion batteries for electric vehicles?",
            "expected_answer": "Không đủ bằng chứng để trả lời.", "gold": []
        },
        {
            "id": "adv_test_abs_03", "split": "test", "group": "abstention",
            "question": "What are the international maritime safety regulations enacted in 2026 for automated seaweed harvesting drones?",
            "expected_answer": "Không đủ bằng chứng để trả lời.", "gold": []
        },
        {
            "id": "adv_test_abs_04", "split": "test", "group": "abstention",
            "question": "What are the protocol guidelines for cultivating commercial kelp inside lunar soil greenhouses on the Moon?",
            "expected_answer": "Không đủ bằng chứng để trả lời.", "gold": []
        },
        {
            "id": "adv_test_abs_05", "split": "test", "group": "abstention",
            "question": "Which cryptocurrency or blockchain network is used by the FAO to verify organic seaweed export certificates?",
            "expected_answer": "Không đủ bằng chứng để trả lời.", "gold": []
        },
        {
            "id": "adv_test_abs_06", "split": "test", "group": "abstention",
            "question": "What is the concentration of titanium nanoparticles added to edible nori sheets to increase tensile strength?",
            "expected_answer": "Không đủ bằng chứng để trả lời.", "gold": []
        }
    ]

    all_advanced = dev_questions + test_questions
    out_file = Path("data/benchmark_advanced.json")
    out_file.write_text(json.dumps(all_advanced, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Đã tạo thành công {out_file}: {len(dev_questions)} câu dev và {len(test_questions)} câu test!")


if __name__ == "__main__":
    main()
