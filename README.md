#  Relatório Final - LAB03  

## 1. Informações do grupo  
- ** Curso:** Engenharia de Software  
- ** Disciplina:** Laboratório de Experimentação de Software  
- ** Período:** 6° Período  
- ** Professor(a):** Prof. Dr. João Paulo Carneiro Aramuni  
- ** Membros do Grupo:** Arthur Ferreira, Kimberly Liz, Renato Cazzoletti  

---

## 2. Introdução  

Neste laboratório, o objetivo foi **caracterizar a atividade de *code review* no GitHub**, analisando métricas associadas a *Pull Requests (PRs)*. Essa prática é essencial em projetos de software colaborativos, pois permite identificar defeitos, promover discussões técnicas e melhorar a qualidade do código antes da integração.  

A proposta do experimento foi investigar **como diferentes características dos PRs** — como tamanho, tempo de análise, número de interações e detalhamento da descrição — estão relacionadas ao resultado final (MERGED ou CLOSED) e à quantidade de revisões recebidas.  

Com base nos dados disponibilizados, formulamos hipóteses informais e conduzimos uma análise estatística para verificar se tais relações se confirmam, buscando compreender quais fatores influenciam o sucesso e a dinâmica das revisões de código.

---

## 3. Tecnologias e ferramentas utilizadas  

A coleta e análise dos dados foram realizadas utilizando um conjunto de bibliotecas e tecnologias específicas para interação com a API do GitHub e processamento estatístico.  

- ** Linguagem:** Python 3.x  
- ** Bibliotecas principais:**  
  - `requests` e `gql` — para comunicação com a **GitHub GraphQL API**;  
  - `pandas` — manipulação e estruturação dos dados em formato tabular (DataFrame e CSV);  
  - `numpy` — suporte a operações numéricas e vetoriais;  
  - `scipy` — aplicação dos testes estatísticos (Spearman e Mann–Whitney U);  
  - `matplotlib` — geração dos gráficos de análise;  
  - `dotenv` — leitura segura do token de autenticação do arquivo `.env`;  
  - `concurrent.futures` — execução **paralela** para coleta de PRs em múltiplos repositórios simultaneamente.  

- ** API utilizada:**  
  - **GitHub GraphQL API v4**, acessada via autenticação por token pessoal, permitindo consultas otimizadas sobre repositórios, *pull requests*, revisões e participantes.  

- ** Estratégias de execução:**  
  - Coleta dos **repositórios mais populares** (≥ 1000 estrelas), com paginação configurada e tratamento de *rate limits* via **backoff exponencial**;  
  - Uso de **multithreading (ThreadPoolExecutor)** para coletar PRs em paralelo, reduzindo o tempo total de execução;  
  - Filtragem automática dos *Pull Requests* conforme critérios definidos (≥ 1 revisão e tempo > 1 hora);  
  - Salvamento incremental em CSV (`pull_requests.csv`), permitindo retomada segura em caso de falha.  

- ** Ferramentas de análise estatística:**  
  - Teste de **correlação de Spearman** — para medir a força e direção das relações entre métricas quantitativas;  
  - Teste **Mann–Whitney U** — para comparar distribuições entre grupos categóricos (MERGED vs CLOSED).  

- ** Visualização:**  
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
**Interpretação:**  
- O gráfico mostra que PRs maiores não têm relação clara com o feedback final (MERGED ou CLOSED). A distribuição é muito concentrada próxima a zero e com poucos outliers grandes.
- Conclusão: Não há correlação significativa entre o tamanho do PR e o feedback final.
<img width="2400" height="1800" alt="image" src="https://github.com/user-attachments/assets/629ab04a-011a-433e-88ac-42d2595e4351" />

---

### 🔹 RQ02 — Relação entre o tempo de análise e o feedback final

**Interpretação:**
- Os PRs fechados (CLOSED) tendem a ter tempos de análise um pouco maiores, mas a sobreposição dos dados é grande.
- Conclusão: Correlação fraca — o tempo de análise não é um fator determinante no feedback final.


<img width="2400" height="1800" alt="image" src="https://github.com/user-attachments/assets/6f854614-7cc9-4938-aac4-631ca1117f11" />



---

### 🔹 RQ03 — Relação entre o tamanho da descrição e o feedback final

**Interpretação:**    
- A quantidade de texto na descrição (pr_description_len) varia pouco entre PRs aceitos e rejeitados, indicando que descrições longas não garantem aprovação.
- Conclusão: Sem correlação significativa entre o tamanho da descrição e o feedback final.

<img width="2400" height="1800" alt="image" src="https://github.com/user-attachments/assets/10f50045-a4fc-4501-a378-c3386811adb7" />





---

### 🔹 RQ04 — Relação entre as interações e o feedback final

**Interpretação:**  

- Os PRs com mais interações aparecem tanto em MERGED quanto em CLOSED, sem padrão claro.
- Conclusão: Não há correlação evidente entre o número de interações e o feedback final.

<img width="2400" height="1800" alt="image" src="https://github.com/user-attachments/assets/97539f63-95fc-4110-9447-5d6cdd6892f0" />






---

### 🔹 RQ05 — Tamanho do PR × número de revisões
- Correlação de Spearman (`num_files` × `review_count`): **r = 0.1120**, *p* < 0.001  
<img width="2400" height="1800" alt="image" src="https://github.com/user-attachments/assets/a31f3c00-020f-4c43-a8c3-daf7b4877dd4" />


**Interpretação:**  
Existe uma correlação positiva, embora fraca: PRs maiores tendem a receber mais revisões. Isso é esperado, pois modificações extensas demandam maior validação.

---

### 🔹 RQ06 — Tempo de análise × número de revisões
- Correlação de Spearman: **r = 0.2170**, *p* < 0.001  
<img width="2400" height="1800" alt="image" src="https://github.com/user-attachments/assets/e3e85734-97a9-48df-b8c1-05a2220391ca" />


**Interpretação:**  
Correlação moderada positiva. PRs que demoram mais para serem concluídos geralmente envolvem mais revisões e discussões, sugerindo **processos mais colaborativos** ou **códigos mais complexos**.

---

### 🔹 RQ07 — Tamanho da descrição × número de revisões
- Correlação de Spearman: **r = 0.0580**, *p* < 0.001  
<img width="2400" height="1800" alt="image" src="https://github.com/user-attachments/assets/2259fbb2-06f7-4508-ac72-3e47a6e824af" />


**Interpretação:**  
Correlação fraca, indicando que o comprimento da descrição **não influencia significativamente** o número de revisões. Autores detalhistas não necessariamente reduzem o volume de feedback recebido.

---

### 🔹 RQ08 — Interações × número de revisões
- Correlação de Spearman: **r = 0.4820**, *p* < 0.001  
<img width="2400" height="1800" alt="image" src="https://github.com/user-attachments/assets/86cd8822-c3b9-4bb9-b14e-ca681ff28f9d" />


**Interpretação:**  
Correlação forte. PRs com mais interações possuem mais revisões, o que confirma que **a colaboração é central no processo de revisão**. Projetos com maior engajamento revisam de forma mais intensa.

---

## 6. Discussão das Hipóteses  

Nesta seção, analisamos os resultados obtidos para as cinco hipóteses formuladas a partir das métricas coletadas no processo de *code review* no GitHub.  
Cada hipótese foi testada por meio de correlação de Spearman, de modo a identificar padrões de relação entre variáveis de interesse, e é acompanhada de seu respectivo gráfico de dispersão.

---

### **H1 — Linhas alteradas × Número de revisões**

**Hipótese:** PRs que modificam mais linhas exigem mais revisões, pois são potencialmente mais complexos e demandam maior atenção dos revisores.  

**Resultado:** ⚠️ *Parcialmente confirmada*  
O coeficiente de correlação de Spearman indica uma **relação positiva moderada**, mas não uniforme em todos os casos.  
Isso sugere que PRs muito grandes tendem, de fato, a gerar mais rodadas de revisão, porém há casos em que equipes lidam com PRs extensos de forma eficiente — por exemplo, quando há bom contexto ou documentação.  

**Interpretação:**  
Esse comportamento pode refletir a maturidade dos projetos: repositórios mais organizados mantêm diretrizes claras de contribuição, o que reduz a necessidade de revisões extras mesmo para grandes alterações.  
Ainda assim, o aumento de linhas modificadas tende a elevar o esforço de revisão e o risco de rejeição parcial.  

 **Gráfico — H1: Linhas alteradas × Nº de revisões**  
<img width="2400" height="1800" alt="image" src="https://github.com/user-attachments/assets/e0c04645-14a2-4fc6-83e4-179cb0cad037" />


---

### **H2 — Tempo de análise × Número de revisões**

**Hipótese:** PRs que permanecem mais tempo em revisão passam por mais ciclos de avaliação, o que aumenta o número total de revisões registradas.  

**Resultado:** ✅ *Confirmada*  
A análise revelou uma **correlação positiva significativa**, mostrando que revisões mais longas tendem a envolver mais discussões e iterações.  

**Interpretação:**  
Esse resultado reforça a ideia de que revisões detalhadas levam tempo, e que o tempo de permanência de um PR em análise reflete a profundidade da revisão.  
PRs que passam por várias rodadas geralmente envolvem mais pessoas e comentários, o que está alinhado com práticas de qualidade em desenvolvimento colaborativo.  

 **Gráfico — H2: Tempo de análise × Nº de revisões**  
<img width="2400" height="1800" alt="image" src="https://github.com/user-attachments/assets/819ac273-3c9a-4b58-8797-6d15200f02e2" />


---

### **H3 — Tamanho da descrição × Número de revisões**

**Hipótese:** Descrições mais completas reduzem o número de revisões, pois facilitam o entendimento do contexto pelo revisor.  

**Resultado:** ❌ *Refutada*  
Os resultados mostraram **correlação fraca e positiva**, ou seja, descrições mais longas estão associadas a um pequeno aumento no número de revisões.  

**Interpretação:**  
Esse achado contraria a expectativa inicial: PRs com descrições mais detalhadas não necessariamente simplificam o processo.  
Na prática, descrições longas podem sinalizar PRs mais complexos, o que demanda mais comentários, discussões e ajustes antes da aprovação.  

 **Gráfico — H3: Descrição × Nº de revisões**  
<img width="2400" height="1800" alt="image" src="https://github.com/user-attachments/assets/b9034327-a3f8-4364-ac32-8cd2d2df2556" />


---

### **H4 — Interações × Número de revisões**

**Hipótese:** PRs com mais interações (comentários e discussões) tendem a ter mais revisões, pois há maior engajamento entre autor e revisores.  

**Resultado:** ✅ *Confirmada*  
A correlação de Spearman foi **forte e positiva**, indicando que interações e número de revisões crescem em conjunto.  

**Interpretação:**  
Isso evidencia o papel da comunicação no processo de revisão: quanto maior o diálogo entre os envolvidos, mais o PR é aprimorado.  
Projetos colaborativos com cultura de revisão ativa tendem a exibir esse padrão, associando mais interações a melhores resultados e maior probabilidade de *merge*.  

 **Gráfico — H4: Interações × Revisões**  
<img width="2400" height="1800" alt="image" src="https://github.com/user-attachments/assets/1a0e1f61-9afe-4a88-8a86-da9f6135a952" />


---

### **H5 — Arquivos modificados × Linhas alteradas**

**Hipótese:** PRs que alteram mais arquivos também modificam mais linhas, pois mudanças amplas tendem a impactar múltiplos componentes.  

**Resultado:** ✅ *Confirmada*  
A correlação de Spearman foi **forte (ρ ≈ 0.73)**, indicando uma relação direta e consistente entre o número de arquivos e a quantidade de linhas modificadas.  

**Interpretação:**  
Esse é um dos resultados mais claros e intuitivos: quanto mais arquivos são afetados, maior o volume total de código alterado.  
A relação linear indica que essas alterações são distribuídas de forma coerente e refletem a complexidade estrutural dos PRs.  
Além disso, o padrão confirma que *pull requests* mais amplos impactam mais partes do sistema, exigindo revisões cuidadosas.  

 **Gráfico — H5: Arquivos × Linhas alteradas**  
<img width="2400" height="1800" alt="image" src="https://github.com/user-attachments/assets/70e59e61-1a05-46c5-879b-a26834abbcbd" />


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

Link da apresentação: [Acesse aqui](https://docs.google.com/presentation/d/1KO-RxrJjtQDP-SK9_D4d-fQG5G9AKngT9UdIoiG09P4/edit?usp=sharing)

