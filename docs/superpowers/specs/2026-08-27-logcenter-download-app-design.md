# LogCenter Download — Design

## Contexto e objetivo

App Flask interna para rodar aggregations do MongoDB Atlas e baixar o
resultado (CSV/Excel/JSON), com um datepicker personalizado para o campo
`timestamp` e a possibilidade de favoritar pipelines usados com frequência.
Duas telas: **Login** e **Download**. Estilo visual segue o design system
DreamBricks (`design_system/`).

Não há autenticação/usuário previamente definidos no projeto nem código
existente — é um app novo, do zero.

## Fora de escopo

- Escolha de banco/collection na UI (fixo via `.env`).
- Múltiplos usuários com cadastro/hash de senha (um único usuário fixo).
- Escrita no banco (`$out`/`$merge` são explicitamente bloqueados — app é
  somente leitura/exportação).
- Paginação/streaming de resultados muito grandes (assume volumes de uso
  interno, cabendo em memória).

## Arquitetura

Flask "server-rendered" (Jinja2 + JS vanilla), sem build step/React. O
design system fornecido é uma biblioteca de componentes React — para esta
app os tokens CSS (`tokens/*.css`) e os SVGs de logo são reaproveitados
diretamente, e os componentes (Button, Input, Card, Tag, Dialog) são
recriados como classes CSS simples fiéis às mesmas decisões visuais
(cor, raio, sombra, tipografia, espaçamento).

```
logcenter_download/
  app.py                     # rotas Flask
  config.py                  # le .env (MONGODB_URI, DB_NAME, COLLECTION_NAME,
                              #           APP_USERNAME, APP_PASSWORD, SECRET_KEY)
  requirements.txt
  .env.example
  services/
    mongo_client.py          # conexao pymongo + run_aggregation()
    pipeline_parser.py       # parser tolerante (shell/Compass -> pipeline pymongo)
    export.py                # gera csv / xlsx / json a partir do resultado
  templates/
    base.html
    login.html
    download.html
  static/
    css/                     # tokens copiados de design_system/ + app.css
    js/                      # datepicker.js, favorites.js, app.js
    img/                     # logo copiado de design_system/assets
  favorites/                 # arquivos estaticos .json dos favoritos salvos
  tests/
    test_pipeline_parser.py
```

## Autenticação

- Usuário e senha únicos, fixos via variáveis de ambiente
  `APP_USERNAME` / `APP_PASSWORD`.
- `POST /login`: compara credenciais com `secrets.compare_digest`
  (evita timing attack), seta `session['logged_in'] = True` em caso de
  sucesso, redireciona para `/download`.
- Erro de login: mensagem genérica inline no formulário (não indica se foi
  usuário ou senha incorretos).
- Decorator `@login_required` protege `/download` e todas as rotas
  `/api/*` e `/download/<formato>` — sem sessão válida, redireciona para
  `/login`.
- `GET /logout` limpa a sessão e redireciona para `/login`.
- `SECRET_KEY` da sessão Flask também vem do `.env`.

## Tela Download

Layout: header com logo DreamBricks + botão sair; conteúdo em duas
colunas — editor/preview à esquerda, sidebar de favoritos à direita.

### Editor de aggregation

- `<textarea>` monoespaçado (`--font-mono`), aceita colar o pipeline
  exatamente como copiado do Compass/shell: chaves sem aspas,
  `ObjectId("...")`, comentários `//`, linhas comentadas.
- Pré-preenchido com um pipeline de exemplo (o mesmo do enunciado, sem o
  `project_id` real) para orientar o formato esperado.

### Datepicker personalizado

- Widget acima do editor com toggle **Dia único** / **Intervalo**.
- Dia único: um único calendário; ao confirmar, gera
  `timestamp: { $regex: "^AAAA-MM-DD" }`.
- Intervalo: dois calendários (início/fim); ao confirmar, gera
  `timestamp: { $gte: ISODate("AAAA-MM-DDT00:00:00Z"), $lt: ISODate("AAAA-MM-DDT00:00:00Z") }`
  (fim exclusivo = dia seguinte à data final escolhida, para incluir o dia
  inteiro).
- Botão **Aplicar data**: roda no cliente (JS), localiza via regex a
  primeira linha que casa com `/^\s*\/{0,2}\s*timestamp\s*:/` dentro do
  texto do editor (comentada ou não) e substitui a linha inteira pela
  cláusula gerada, sem comentário. Se nenhuma linha `timestamp` for
  encontrada, insere a cláusula como primeira linha do corpo do primeiro
  estágio `$match: {` encontrado no texto.
- Se não houver nenhum `$match` no texto, mostra erro inline e não altera
  o editor.

### Executar

- Botão **Executar** → `POST /api/run` com `{ pipeline: <texto> }`.
- Backend: `pipeline_parser.parse(texto)` → lista de estágios;
  `mongo_client.run_aggregation(stages)` → lista de documentos.
- Resposta: `{ columns: [...], rows: [...], count: N }` (colunas
  inferidas da união das chaves dos documentos retornados, na ordem de
  primeira aparição).
- Frontend renderiza tabela de preview com as colunas/linhas e a
  contagem total. Erros de parsing ou de execução no Mongo aparecem como
  banner de erro inline, sem derrubar a página nem limpar o editor.
- Resultado vazio (`count == 0`): tabela mostra estado vazio
  ("Nenhum resultado encontrado"), botões de download ficam desabilitados.

### Download

- Três botões: **CSV**, **Excel**, **JSON** — habilitados só após uma
  execução com `count > 0`.
- Cada botão faz `POST /download/<formato>` reenviando o texto atual do
  editor (campo oculto sincronizado com o textarea). O backend reexecuta
  o parser + a aggregation (sem estado de sessão intermediário) e faz
  stream do arquivo gerado (`services/export.py`) com
  `Content-Disposition: attachment`.
- Nome do arquivo: `logcenter_<timestamp-atual>.<ext>`.

### Favoritos

- Botão **Favoritar** abre um modal (componente `Dialog` do design
  system) pedindo um nome; ao confirmar, `POST /api/favorites` salva
  `favorites/<slug-do-nome>-<timestamp>.json` com
  `{ name, pipeline, created_at }`.
- Sidebar carrega a lista via `GET /api/favorites` (nome + data, mais
  recentes primeiro) e re-lista após favoritar/excluir.
- Clicar em um favorito carrega seu `pipeline` no editor (substitui o
  conteúdo atual, sem confirmação extra — é uma troca de rascunho, não
  uma ação destrutiva de dados salvos).
- Ícone de lixeira por item → `DELETE /api/favorites/<arquivo>` remove o
  arquivo correspondente.
- Nomes duplicados são permitidos (o slug+timestamp no nome do arquivo
  evita colisão).

## Parser de pipeline (`services/pipeline_parser.py`)

Converte o texto colado (formato shell/Compass) em uma lista de estágios
válida para o PyMongo:

1. Remove comentários de linha `//` (um parser char-a-char que ignora `//`
   quando está dentro de uma string `"..."`, para não corromper valores
   que contenham `//`, como URLs).
2. Substitui `ObjectId("<hex24>")` → `{"$oid": "<hex24>"}`.
3. Substitui `ISODate("<iso>")` → `{"$date": "<iso>"}`.
4. Regex adiciona aspas em chaves não citadas, incluindo operadores
   (`$match`, `$gt`, `$ifNull`, etc): identifica tokens
   `([A-Za-z_$][A-Za-z0-9_$]*)\s*:` em posição de chave e envolve em
   aspas.
5. `bson.json_util.loads(...)` interpreta o JSON estendido resultante,
   convertendo `$oid`/`$date` em `ObjectId`/`datetime` reais.
6. Valida que o resultado é uma `list` de `dict`s (estágios). Caso
   contrário, levanta erro com mensagem clara.
7. Rejeita pipelines que contenham estágio `$out` ou `$merge` (app é
   somente leitura) — levanta erro explicando que exportação de dados
   para o banco não é permitida por esta ferramenta.

Qualquer falha nesse processo (JSON malformado, chave sem valor,
`ObjectId` inválido, estágio proibido) retorna uma mensagem de erro
específica para exibição inline — nunca um 500 genérico.

## Conexão MongoDB

- `services/mongo_client.py`: cliente `pymongo.MongoClient(MONGODB_URI)`
  criado uma vez (nível de módulo/app), reaproveitado entre requisições.
- `run_aggregation(stages)` roda
  `client[DB_NAME][COLLECTION_NAME].aggregate(stages)` e retorna
  `list(cursor)`.
- Falha de conexão/autenticação com o Atlas → capturada e traduzida em
  banner de erro ("Não foi possível conectar ao MongoDB Atlas. Verifique
  MONGODB_URI.") — sem expor a connection string ou stacktrace ao
  usuário.

## Exportação (`services/export.py`)

A partir da mesma `list[dict]` retornada pela aggregation:

- **CSV**: `csv.DictWriter` (stdlib), colunas = união das chaves na ordem
  de primeira aparição; valores não-primitivos (ex.: sub-documentos)
  serializados como JSON string na célula.
- **Excel**: `openpyxl`, mesma lógica de colunas; uma planilha única.
- **JSON**: `bson.json_util.dumps` do resultado bruto (preserva tipos
  como datas/ObjectId de forma legível), formatado (`indent=2`).

## Estilo visual

- CSS copiado/derivado de `design_system/tokens/{colors,spacing,typography,fonts}.css`.
- Logo: `dreambricks-horizontal-onlight.svg` no header da tela Download e
  no topo do card de login; `dreambricks-mark-blue.svg` como favicon.
- Componentes recriados como classes CSS puras equivalentes aos `.jsx`
  do design system: `.btn` (variantes primary/secondary/ghost/danger,
  tamanhos sm/md/lg), `.input`, `.card` (`--radius-lg`, `--shadow-sm`,
  hover `--shadow-md`), `.tag`, `.dialog` (modal de favoritar).
  Ícones via Lucide CDN (mesmo padrão do design system).
- Fundo de página com `--surface-page`, cards com `--surface-card`,
  paleta azul da marca para ações primárias (Executar, Entrar).

## Erros e estados — resumo

| Situação | Comportamento |
|---|---|
| Falha ao conectar no MongoDB Atlas | Banner de erro no topo da tela Download |
| Pipeline com sintaxe inválida | Erro inline abaixo do editor, editor mantém o texto digitado |
| Pipeline com `$out`/`$merge` | Erro inline explicando que a ferramenta é somente leitura |
| Datepicker sem `$match` no texto | Erro inline no widget de data, editor não é alterado |
| Resultado vazio | Estado vazio na área de preview, botões de download desabilitados |
| Login inválido | Erro inline genérico no formulário de login |
| Sessão expirada/ausente | Redireciona para `/login` |

## Testes

- `tests/test_pipeline_parser.py` (pytest): casos para o texto de
  exemplo do enunciado (com comentários e `ObjectId`), `ISODate`,
  pipeline JSON estrito já válido, JSON malformado, pipeline com `$out`
  (deve rejeitar), pipeline que não é uma lista.
- Verificação manual no navegador (via skill `run`) após a implementação:
  login com credenciais corretas/incorretas, aplicar datepicker
  (dia único e intervalo) sobre o texto de exemplo, executar e ver
  preview, favoritar/carregar/excluir favorito, baixar nos três formatos.
- Sem testes automatizados de integração com o MongoDB Atlas real (exige
  credenciais/dados de um projeto específico) — validado manualmente
  contra o Atlas do usuário.
