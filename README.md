#  Relatório Final - LAB03  

## 1. Informações do grupo  
- **🎓 Curso:** Engenharia de Software  
- **📘 Disciplina:** Laboratório de Experimentação de Software  
- **🗓 Período:** 6° Período  
- **👨‍🏫 Professor(a):** Prof. Dr. João Paulo Carneiro Aramuni  
- **👥 Membros do Grupo:** Arthur Ferreira, Kimberly Liz, Renato Cazzoletti  

---

## 2. Introdução  

Neste laboratório, o objetivo foi **caracterizar a atividade de *code review* no GitHub**, analisando métricas associadas a *Pull Requests (PRs)*. Essa prática é essencial em projetos de software colaborativos, pois permite identificar defeitos, promover discussões técnicas e melhorar a qualidade do código antes da integração.  

A proposta do experimento foi investigar **como diferentes características dos PRs** — como tamanho, tempo de análise, número de interações e detalhamento da descrição — estão relacionadas ao resultado final (MERGED ou CLOSED) e à quantidade de revisões recebidas.  

Com base nos dados disponibilizados, formulamos hipóteses informais e conduzimos uma análise estatística para verificar se tais relações se confirmam, buscando compreender quais fatores influenciam o sucesso e a dinâmica das revisões de código.

---

## 3. Tecnologias e ferramentas utilizadas  

A coleta e análise dos dados foram realizadas utilizando um conjunto de bibliotecas e tecnologias específicas para interação com a API do GitHub e processamento estatístico.  

- **💻 Linguagem:** Python 3.x  
- **📦 Bibliotecas principais:**  
  - `requests` e `gql` — para comunicação com a **GitHub GraphQL API**;  
  - `pandas` — manipulação e estruturação dos dados em formato tabular (DataFrame e CSV);  
  - `numpy` — suporte a operações numéricas e vetoriais;  
  - `scipy` — aplicação dos testes estatísticos (Spearman e Mann–Whitney U);  
  - `matplotlib` — geração dos gráficos de análise;  
  - `dotenv` — leitura segura do token de autenticação do arquivo `.env`;  
  - `concurrent.futures` — execução **paralela** para coleta de PRs em múltiplos repositórios simultaneamente.  

- **🌐 API utilizada:**  
  - **GitHub GraphQL API v4**, acessada via autenticação por token pessoal, permitindo consultas otimizadas sobre repositórios, *pull requests*, revisões e participantes.  

- **⚙️ Estratégias de execução:**  
  - Coleta dos **repositórios mais populares** (≥ 1000 estrelas), com paginação configurada e tratamento de *rate limits* via **backoff exponencial**;  
  - Uso de **multithreading (ThreadPoolExecutor)** para coletar PRs em paralelo, reduzindo o tempo total de execução;  
  - Filtragem automática dos *Pull Requests* conforme critérios definidos (≥ 1 revisão e tempo > 1 hora);  
  - Salvamento incremental em CSV (`pull_requests.csv`), permitindo retomada segura em caso de falha.  

- **🧠 Ferramentas de análise estatística:**  
  - Teste de **correlação de Spearman** — para medir a força e direção das relações entre métricas quantitativas;  
  - Teste **Mann–Whitney U** — para comparar distribuições entre grupos categóricos (MERGED vs CLOSED).  

- **🖼 Visualização:**  
  - Geração de gráficos por questão de pesquisa (RQ01–RQ08) e hipóteses (H1–H5), com **boxplots e dispersões**, para apoiar a interpretação visual das tendências.  

---


## 4. Metodologia  

### 4.1 Coleta e pré-processamento de dados  
O conjunto de dados analisado foi obtido via **GitHub GraphQL API**, contendo métricas por *Pull Request*. Inicialmente, realizou-se um pré-processamento para normalizar nomes de colunas, converter datas (`createdAt` e `closedAt`) e remover valores inconsistentes.  

A partir dos dados brutos, criaram-se métricas derivadas:  
- `lines_changed = additions + deletions` → quantifica o tamanho total da modificação;  
- `interactions = participants + comments` → representa o engajamento no processo de revisão;  
- `desc_len` → comprimento da descrição em caracteres, indicando detalhamento do autor;  
- `analysis_time_hours` → tempo entre abertura e fechamento do PR.  

Em seguida, aplicaram-se filtros para garantir a qualidade da amostra:
- PRs com **status MERGED ou CLOSED**;  
- pelo menos **1 revisão registrada** (`review_count ≥ 1`);  
- **tempo de análise > 1 hora**, excluindo revisões automáticas ou triviais.  

Após os filtros, restaram **16.094 PRs válidos** para análise.

---

### 4.2 Hipóteses informais  

1. **H1:** PRs com mais linhas alteradas tendem a ser menos frequentemente *MERGED*.  
2. **H2:** PRs com maior tempo de análise têm mais chance de serem *MERGED*.  
3. **H3:** PRs com descrições mais longas possuem menos revisões.  
4. **H4:** PRs com mais interações (comentários + participantes) recebem mais revisões.  
5. **H5:** PRs que alteram mais arquivos também alteram mais linhas (forte correlação entre tamanho e impacto).  

---

### 4.3 Procedimentos estatísticos e justificativa  

Para avaliar as relações entre as variáveis quantitativas, utilizamos o **teste de correlação de Spearman**.  

**Justificativa:**  
- O teste de **Spearman** é uma medida **não-paramétrica** de correlação, ou seja, não exige que os dados sigam uma distribuição normal.  
- Ele avalia a **relação monotônica** entre variáveis, sendo adequado para métricas de software que geralmente são assimétricas e com *outliers* (como número de linhas alteradas e tempo de análise).  
- Já o **teste de Pearson** pressupõe linearidade e normalidade — condições raramente satisfeitas em dados de engenharia de software.  

Assim, o uso de Spearman garante **maior robustez e confiança** nas análises, evitando distorções causadas por valores extremos.  

Além disso:  
- Para comparar distribuições entre dois grupos categóricos (MERGED vs CLOSED), utilizou-se o **teste de Mann–Whitney U**, também não-paramétrico, adequado para amostras de tamanhos diferentes.  
- As análises foram conduzidas no Python utilizando as funções `scipy.stats.spearmanr()` e `mannwhitneyu()`.  

---

### 4.4 Métricas analisadas  

| Métrica | Descrição | Tipo |
|----------|------------|------|
| `num_files` | Número de arquivos alterados | Quantitativa |
| `lines_changed` | Soma de linhas adicionadas e removidas | Quantitativa |
| `analysis_time_hours` | Tempo entre abertura e fechamento do PR | Quantitativa |
| `desc_len` | Comprimento da descrição (caracteres) | Quantitativa |
| `interactions` | Participantes + comentários | Quantitativa |
| `review_count` | Total de revisões realizadas | Quantitativa |
| `status_norm` | Resultado final do PR (MERGED/CLOSED) | Categórica |

---

### 4.5 Interpretação das estatísticas  

As análises utilizaram duas principais medidas estatísticas:  

**ρ de Spearman (Rho de Spearman):**  
Indica a força e a direção da relação entre duas variáveis.  

| Intervalo de ρ | Interpretação |
|-----------------|----------------|
| **-1 a -0.7** | Correlação negativa forte |
| **-0.7 a -0.3** | Correlação negativa moderada |
| **-0.3 a 0.3** | Correlação fraca ou inexistente |
| **0.3 a 0.7** | Correlação positiva moderada |
| **0.7 a 1** | Correlação positiva forte |

**p-valor:**  
Indica se a correlação observada é estatisticamente significativa:  
- **p < 0.05:** Correlação significativa (confiável)  
- **p ≥ 0.05:** Correlação não significativa (pode ser coincidência)  

Essas medidas combinadas permitem interpretar se as relações encontradas são **relevantes, confiáveis e consistentes** dentro do contexto analisado.

---

## 5. Resultados obtidos  

Após aplicar os filtros, foram analisados **16.094 Pull Requests**.  
Os resultados foram organizados conforme as **questões de pesquisa (RQ)** propostas no enunciado do laboratório.

### 🔹 RQ01 — Relação entre o tamanho dos PRs e o feedback final
- Mediana de `num_files`: **MERGED = 1**, **CLOSED = 1**  
- Mediana de `lines_changed`: **MERGED = 61**, **CLOSED = 64**  
📊 *Figura:* `figs_lab03/RQ01_lines_by_status.png`  

**Interpretação:**  
Não houve diferença significativa entre PRs aceitos e rejeitados em termos de tamanho. Isso indica que o número de arquivos ou linhas modificadas **não é o fator determinante** para o merge, sugerindo que revisores consideram mais a qualidade e relevância das mudanças do que a quantidade de linhas.

---

### 🔹 RQ02 — Relação entre o tempo de análise e o feedback final
- Mediana de `analysis_time_hours`: **MERGED = 24 h**, **CLOSED = 22 h**  
📊 *Figura:* `figs_lab03/RQ02_time_by_status.png`

**Interpretação:**  
PRs *MERGED* apresentaram tempo ligeiramente maior de análise. Isso sugere que **revisões mais longas tendem a ser mais cuidadosas e colaborativas**, o que pode favorecer a aceitação final do código.

---

### 🔹 RQ03 — Relação entre o tamanho da descrição e o feedback final
- Mediana de `desc_len`: **MERGED = 326**, **CLOSED = 304**  
📊 *Figura:* `figs_lab03/RQ03_desc_by_status.png`

**Interpretação:**  
Descrições mais longas aparecem em PRs *MERGED*, ainda que a diferença seja pequena. Isso sugere que descrições detalhadas podem **facilitar a compreensão** dos revisores e aumentar a chance de aprovação.

---

### 🔹 RQ04 — Relação entre as interações e o feedback final
- Mediana de `interactions`: **MERGED = 4**, **CLOSED = 3**  
📊 *Figura:* `figs_lab03/RQ04_interactions_by_status.png`

**Interpretação:**  
PRs aceitos tendem a envolver **mais interações**, indicando que o engajamento durante o processo de revisão é um fator positivo. A discussão entre revisores e autores parece estar relacionada à qualidade e aceitação final do PR.

---

### 🔹 RQ05 — Tamanho do PR × número de revisões
- Correlação de Spearman (`num_files` × `review_count`): **r = 0.1120**, *p* < 0.001  
📊 *Figura:* `figs_lab03/RQ05_files_vs_reviews.png`

**Interpretação:**  
Existe uma correlação positiva, embora fraca: PRs maiores tendem a receber mais revisões. Isso é esperado, pois modificações extensas demandam maior validação.

---

### 🔹 RQ06 — Tempo de análise × número de revisões
- Correlação de Spearman: **r = 0.2170**, *p* < 0.001  
📊 *Figura:* `figs_lab03/RQ06_time_vs_reviews.png`

**Interpretação:**  
Correlação moderada positiva. PRs que demoram mais para serem concluídos geralmente envolvem mais revisões e discussões, sugerindo **processos mais colaborativos** ou **códigos mais complexos**.

---

### 🔹 RQ07 — Tamanho da descrição × número de revisões
- Correlação de Spearman: **r = 0.0580**, *p* < 0.001  
📊 *Figura:* `figs_lab03/RQ07_desc_vs_reviews.png`

**Interpretação:**  
Correlação fraca, indicando que o comprimento da descrição **não influencia significativamente** o número de revisões. Autores detalhistas não necessariamente reduzem o volume de feedback recebido.

---

### 🔹 RQ08 — Interações × número de revisões
- Correlação de Spearman: **r = 0.4820**, *p* < 0.001  
📊 *Figura:* `figs_lab03/RQ08_interactions_vs_reviews.png`

**Interpretação:**  
Correlação forte. PRs com mais interações possuem mais revisões, o que confirma que **a colaboração é central no processo de revisão**. Projetos com maior engajamento revisam de forma mais intensa.

---

## 6. Discussão das hipóteses  

| Hipótese | Resultado | Interpretação detalhada |
|-----------|------------|-------------------------|
| **H1** | ❌ *Refutada* | PRs grandes não foram necessariamente rejeitados — revisores parecem priorizar qualidade e contexto das alterações. |
| **H2** | ⚠️ *Parcialmente confirmada* | Revisões mais longas indicam maior discussão e revisão colaborativa, o que aumenta as chances de merge. |
| **H3** | ❌ *Refutada* | Descrições longas não reduzem revisões; ao contrário, PRs complexos exigem mais explicação e mais feedback. |
| **H4** | ✅ *Confirmada* | Interações e revisões estão fortemente ligadas — quanto mais diálogo entre revisores e autores, mais revisões são registradas. |
| **H5** | ✅ *Confirmada* | Correlação alta (r ≈ 0.73) mostra que PRs com mais arquivos alteram mais linhas, refletindo maior impacto e complexidade. |

---

## 7. Conclusão  

O experimento mostrou que as métricas de *Pull Requests* refletem aspectos importantes da dinâmica colaborativa em projetos open source.  
A aceitação de um PR depende menos do seu tamanho e mais da **interação e comunicação entre desenvolvedores**.  

Revisões com maior engajamento e tempo de análise tendem a resultar em merges bem-sucedidos, reforçando o papel do *code review* como prática de melhoria contínua.  

---

## 8. Limitações e trabalhos futuros  

- As análises não consideraram linguagem, tipo de projeto ou perfil dos contribuidores.  
- Correlações não indicam causalidade: relações observadas podem ser indiretas.  
- O conjunto de dados agrega PRs de múltiplos repositórios, podendo conter vieses de domínio.  
- Trabalhos futuros podem aplicar **modelos preditivos** (ex.: regressão logística) para estimar a probabilidade de merge com base nas métricas analisadas.  

---

