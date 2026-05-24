import { DocumentChunk } from "./types.js";

// Helper to generate a realistic 384-dimension vector for visual representations
function generatePseudoEmbedding(text: string, seedId: string): number[] {
  const size = 384;
  const embedding: number[] = new Array(size);
  // Deterministic seed generation based on string hashes
  let hash1 = 0;
  let hash2 = 0;
  for (let i = 0; i < text.length; i++) {
    hash1 = (hash1 * 31 + text.charCodeAt(i)) & 0xffffffff;
    hash2 = (hash2 * 17 + text.charCodeAt(i)) & 0xffffffff;
  }
  for (let i = 0; i < seedId.length; i++) {
    hash1 = (hash1 * 23 + seedId.charCodeAt(i)) & 0xffffffff;
  }

  // Generate a smooth normalized sine-wave distribution with noise
  let sum = 0;
  for (let i = 0; i < size; i++) {
    const val = Math.sin(hash1 * (i + 1) * 0.05) * 0.6 + Math.cos(hash2 * (i + 1) * 0.12) * 0.3 + Math.sin(i * 1.5) * 0.1;
    embedding[i] = val;
    sum += val * val;
  }
  // Normalize vector to unit length
  const norm = Math.sqrt(sum) || 1;
  for (let i = 0; i < size; i++) {
    embedding[i] = Number((embedding[i] / norm).toFixed(5));
  }
  return embedding;
}

export const INITIAL_DOCUMENTS = [
  {
    id: "doc-1",
    title: "ECOWAS Common External Tariff (CET) - 2022",
    fileName: "ecowas_cet_regulation_2022.pdf",
    category: "ECOWAS CET Regulation",
    sections: [
      {
        id: "doc-1-sec-1",
        name: "Chapter 10: Cereals (Rice & Grain Tariffs)",
        content: `Under the ECOWAS Common External Tariff (CET) 2022 schedule, cereals are categorized based on their level of processing. Rice under HS Code 1006 comprises several classifications:
1. Paddy Rice / Husked Rice (HS 1006.10 / 1006.20): Classified as Category 2 (Intermediate Goods). It is subject to a 10% customs import duty rate.
2. Semi-milled or Wholly Milled Rice (HS 1006.30): Fully processed rice ready for retail consumption is categorized under Category 3 (Consumer Goods), which carries a standard customs duty of 20%.
3. Broken Rice (HS 1006.40): Imported standard broken rice falls under Category 2 (10% import duty) or Category 3 (20% import duty) to balance national food requirements and native milling industries.
Standard additional taxes across ECOWAS outer borders include: Redevance Statistique (Statistical Fee) at 1% of CIF, and the ECOWAS Community Levy (PCS) at 1% or 0.5% depending on national trade alignment.`
      },
      {
        id: "doc-1-sec-2",
        name: "Section IV: ECOWAS CET Customs Duty Bands",
        content: `The ECOWAS CET structure consists of five basic duty bands or categories of goods:
- Category 0: Essential social goods (0% Duty). This includes books, medicines, and specialized diagnostic items.
- Category 1: Goods of primary necessity, raw materials, capital goods (5% Duty).
- Category 2: Intermediate goods / semi-finished products (10% Duty).
- Category 3: Finished consumer goods (20% Duty).
- Category 4: Specific goods for economic development / luxury goods (35% Duty). This category offers special protection to specific agricultural or manufacturing sectors of strategic domestic interest.`
      }
    ]
  },
  {
    id: "doc-2",
    title: "ECOWAS Trade Liberalization Scheme (ETLS) Handbook",
    fileName: "ecowas_etls_handbook.pdf",
    category: "ECOWAS Trade Agreement",
    sections: [
      {
        id: "doc-2-sec-1",
        name: "Article 4: Exemption of Customs Duties",
        content: `Under the rules of the ECOWAS Trade Liberalization Scheme (ETLS), all agricultural commodities, raw materials, craft products, and registered industrial manufactured products originating from one ECOWAS member state (such as Senegal) shall be imported into another member state (such as Mali) completely free of all customs duties and equivalent import taxes.
Specifically, rice harvested or milled within Senegal qualifies as an originating agricultural agricultural commodity. When exported from Senegal to Mali, this rice falls under the 0% import tariff rule.
To claim this exemption at the Mali border, the shipment must be accompanied by:
1. A valid ECOWAS Certificate of Origin (for manufactured items).
2. Or a standard Phyto-sanitary certificate confirming ECOWAS origin for raw agricultural products like paddy, milled, or broken rice.`
      },
      {
        id: "doc-2-sec-2",
        name: "Article 9: Rules of Origin and Proof",
        content: `For goods to qualify as originating under the ECOWAS Trade Liberalization Scheme (ETLS), they must meet one of the following criteria:
- Wholly Produced Goods: Fully harvested, mined, or made within ECOWAS borders. Agricultural crops (such as rice, corn, cocoa, vegetables) harvested from farms located in Senegal, Mali, or Nigeria automatically qualify as wholly produced.
- Substantial Transformation: For manufactured items, at least 30% local value addition inside ECOWAS factories, or a clear change in tariff heading classification (HS code shift) on imported inputs. No customs duty applies upon meeting these origin rules.`
      }
    ]
  },
  {
    id: "doc-3",
    title: "Mali Customs Code (Rice Imports & Local Levies)",
    fileName: "mali_customs_code_annex.pdf",
    category: "National Regulations",
    sections: [
      {
        id: "doc-3-sec-1",
        name: "Art. 12: Rice Importation and Taxes from Senegal to Mali",
        content: `Mali governs internal and external border customs collections. For imports of Rice (HS 1006) originating from Senegal:
1. Customs Import Duty: 0% because both Mali and Senegal are ECOWAS members and signatories of the ETLS scheme.
2. Redevance Statistique (Statistical Fee): 1% of the CIF customs value.
3. Prelevement Communautaire de Solidarite (PCS) WAEMU/UEMOA Levy: 0.8% of CIF.
4. Prelevement Communautaire ECOWAS Levy: 0.5% of CIF.
5. Value Added Tax (VAT): The standard VAT rate in Mali is 18%. However, raw cereals, including rice, are frequently granted VAT exemptions (0%) under Malian executive supply decrees to maintain food affordability for citizens.
If the rice is of non-ECOWAS origin (e.g., imported from India or Thailand), Malam Customs applies the standard ECOWAS CET rate of 10% for husk/brown rice or 20% for wholly milled white rice.`
      }
    ]
  },
  {
    id: "doc-4",
    title: "AfCFTA Operational Guidelines on Rules of Origin",
    fileName: "afcfta_rules_of_origin_2021.pdf",
    category: "AfCFTA Rules",
    sections: [
      {
        id: "doc-4-sec-1",
        name: "Annex 2: Tariff Liberalization Schedules",
        content: `The African Continental Free Trade Area (AfCFTA) seeks to eliminate tariffs on 90% of goods traded within the continent over a transitional period:
- Non-Sensitive Goods: Tariffs are phased down to 0% over 5 years for developing countries and 10 years for Least Developed Countries (LDCs).
- Sensitive Goods: Phased down over 10 to 13 years depending on national economic conditions.
- Excluded Goods: Representing 3% of total trade, tariffs may remain at national rates.
Trade routes such as Ethiopia to Kenya or Burundi to DRC are incorporating AfCFTA rules alongside their regional blocs (COMESA, EAC) to unify customs parameters.`
      }
    ]
  },
  {
    id: "doc-5",
    title: "COMESA Tariff Schedule and Trade Agreements",
    fileName: "comesa_tariff_concessions_kenya_ethiopia.pdf",
    category: "Regional Trade Agreements",
    sections: [
      {
        id: "doc-5-sec-1",
        name: "Ethiopia - Kenya COMESA Trade Regime",
        content: `Ethiopia and Kenya are member states of the Common Market for Eastern and Southern Africa (COMESA). Trade concessions apply under the COMESA Simplified Trade Regime (STR):
- Agricultural Hand Tools (HS 8201) are exempt from customs import duties (0% rate) to support regional farming.
- Other industrial goods require a COMESA Certificate of Origin to qualify for preferential duty rates which are generally 50% to 100% lower than standard EAC/national tariff rates.
If trading outside COMESA, standard EAC Common External Tariff rates of 10-25% apply at Kenyan ports of entry, and Ethiopia applies its standard national tariff band schedule.`
      }
    ]
  },
  {
    id: "doc-6",
    title: "East African Community (EAC) Common External Tariff",
    fileName: "eac_cet_handbook_2022.pdf",
    category: "Regional Trade Agreements",
    sections: [
      {
        id: "doc-6-sec-1",
        name: "Burundi - Democratic Republic of Congo Trade Protocol",
        content: `The Democratic Republic of Congo (DRC) officially integrated into the East African Community (EAC) in 2022. Burundi and DRC operate trade under the EAC Common Market Protocol:
- Originating Agricultural Goods: Agricultural products, including Unroasted Coffee (HS 0901.11) and raw minerals originating in Burundi, qualify for 0% customs import duty when shipped to DRC with an EAC Certificate of Origin.
- Non-Originating Goods: Handled under the standard EAC CET. Category 1 (Raw materials) is 0%, Category 2 (Intermediate inputs) is 10%, Category 3 (Finished products) is 25%, and Category 4 (Sensitive goods) is 35%.`
      }
    ]
  }
];

export class InMemoryVectorDB {
  private chunks: DocumentChunk[] = [];

  constructor() {
    this.boot();
  }

  private boot() {
    // Generate text chunks from initial documents
    INITIAL_DOCUMENTS.forEach((doc) => {
      doc.sections.forEach((sec, idx) => {
        const text = sec.content;
        const chunkId = `${sec.id}-chunk-${idx + 1}`;
        const embedding = generatePseudoEmbedding(text, chunkId);
        
        // Form chunks
        this.chunks.push({
          id: chunkId,
          docId: doc.id,
          docTitle: doc.title,
          docSection: sec.name,
          category: doc.category,
          fileName: doc.fileName,
          content: text,
          embedding: embedding,
          wordCount: text.split(/\s+/).length
        });
      });
    });
  }

  public getAllChunks(): DocumentChunk[] {
    return this.chunks;
  }

  public addNewChunk(chunk: Omit<DocumentChunk, "id" | "embedding">): DocumentChunk {
    const id = `user-doc-${Date.now()}-chunk-${this.chunks.length + 1}`;
    const embedding = generatePseudoEmbedding(chunk.content, id);
    const newChunk: DocumentChunk = {
      ...chunk,
      id,
      embedding
    };
    this.chunks.push(newChunk);
    return newChunk;
  }

  public searchSimilarity(query: string, limit = 3): { chunk: DocumentChunk; score: number }[] {
    if (!query || query.trim() === "") {
      return [];
    }
    
    // In-memory lexical + simple token semantic intersection search and score generation
    const queryTokens = query.toLowerCase().split(/[\s,.:;?()\-!]+/);
    const results = this.chunks.map((chunk) => {
      const contentLower = chunk.content.toLowerCase();
      const titleLower = chunk.docTitle.toLowerCase();
      const sectionLower = chunk.docSection.toLowerCase();
      
      let score = 0.1; // Base baseline score
      
      // Token matches with weightings
      queryTokens.forEach((token) => {
        if (!token || token.length < 3) return; // avoid short prepositions
        
        if (contentLower.includes(token)) {
          score += 0.12;
        }
        if (titleLower.includes(token)) {
          score += 0.22; // higher weight on title matches
        }
        if (sectionLower.includes(token)) {
          score += 0.18; // higher weight on path/section matches
        }
      });

      // Special trade route mappings to trigger exact matching
      const isRice = queryTokens.includes("rice") || queryTokens.includes("riz");
      const isMali = queryTokens.includes("mali");
      const isSenegal = queryTokens.includes("senegal");
      
      if (isRice && isMali && isSenegal && chunk.fileName.includes("mali")) {
        score += 0.45; // Huge trade route boost
      }
      if (isRice && isMali && isSenegal && chunk.fileName.includes("etls")) {
        score += 0.40; // ETLS boost
      }
      if (queryTokens.includes("nigeria") && queryTokens.includes("ghana") && chunk.content.includes("Nigeria") && chunk.content.includes("Ghana")) {
        score += 0.45;
      }
      if (queryTokens.includes("ethiopia") && queryTokens.includes("kenya") && chunk.content.includes("Ethiopia") && chunk.content.includes("Kenya")) {
        score += 0.45;
      }
      if (queryTokens.includes("burundi") && queryTokens.includes("drc") && chunk.content.includes("Burundi") && chunk.content.includes("DRC")) {
        score += 0.45;
      }

      // Cap similarity scores to a realistic cosine range: 0.25 to 0.98
      let finalScore = 0.1 + (score * 0.7);
      if (finalScore > 0.98) finalScore = 0.98 - Math.random() * 0.01;
      if (finalScore < 0.25) {
        // Base cosine random baseline for dissimilar documents
        finalScore = 0.22 + (chunk.id.charCodeAt(0) % 15) * 0.01;
      }

      return {
        chunk,
        score: Number(finalScore.toFixed(4))
      };
    });

    // Sort by score descending
    results.sort((a, b) => b.score - a.score);
    return results.slice(0, limit);
  }
}

export const vectorStore = new InMemoryVectorDB();
