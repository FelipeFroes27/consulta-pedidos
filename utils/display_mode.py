import streamlit.components.v1 as components


def ativar_modo_exibicao():
    components.html(
        """
        <script>
        (() => {
            const INATIVIDADE_MS = 2 * 60 * 1000;
            const TROCA_TELA_MS = 60 * 1000;
            const TELAS = ["/Cronograma", "/Embarques"];
            const storage = window.parent.localStorage;
            const parentWindow = window.parent;
            const parentDocument = parentWindow.document;

            const agora = () => Date.now();
            const caminhoAtual = () => parentWindow.location.pathname.replace(/\\/$/, "") || "/";

            const registrarAtividade = () => {
                storage.setItem("sistemaUltimoClique", String(agora()));
                storage.removeItem("sistemaModoExibicaoAtivo");
                storage.removeItem("sistemaModoExibicaoIndice");
                storage.removeItem("sistemaModoExibicaoProximaTroca");
            };

            const navegar = (destino) => {
                if (caminhoAtual() === destino) {
                    return;
                }

                parentWindow.location.href = destino;
            };

            const verificar = () => {
                const ultimoClique = Number(storage.getItem("sistemaUltimoClique") || agora());
                if (!storage.getItem("sistemaUltimoClique")) {
                    storage.setItem("sistemaUltimoClique", String(ultimoClique));
                }

                if (agora() - ultimoClique < INATIVIDADE_MS) {
                    return;
                }

                const ativo = storage.getItem("sistemaModoExibicaoAtivo") === "1";
                const telaAtual = caminhoAtual();

                if (!ativo) {
                    const indiceAtual = TELAS.indexOf(telaAtual);
                    const proximoIndice = indiceAtual >= 0 ? (indiceAtual + 1) % TELAS.length : 0;

                    storage.setItem("sistemaModoExibicaoAtivo", "1");
                    storage.setItem("sistemaModoExibicaoIndice", String(proximoIndice));
                    storage.setItem("sistemaModoExibicaoProximaTroca", String(agora() + TROCA_TELA_MS));
                    navegar(TELAS[proximoIndice]);
                    return;
                }

                const proximaTroca = Number(storage.getItem("sistemaModoExibicaoProximaTroca") || 0);
                if (agora() < proximaTroca) {
                    return;
                }

                const indiceAtual = Number(storage.getItem("sistemaModoExibicaoIndice") || 0);
                const proximoIndice = (indiceAtual + 1) % TELAS.length;

                storage.setItem("sistemaModoExibicaoIndice", String(proximoIndice));
                storage.setItem("sistemaModoExibicaoProximaTroca", String(agora() + TROCA_TELA_MS));
                navegar(TELAS[proximoIndice]);
            };

            ["click", "keydown", "touchstart"].forEach((evento) => {
                parentDocument.addEventListener(evento, registrarAtividade, true);
            });

            verificar();
            setInterval(verificar, 1000);
        })();
        </script>
        """,
        height=0,
        width=0,
    )
