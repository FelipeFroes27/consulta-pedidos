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
                storage.removeItem("sistemaModoExibicaoInicio");
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

                let inicioModo = Number(storage.getItem("sistemaModoExibicaoInicio"));
                if (!inicioModo) {
                    inicioModo = agora();
                    storage.setItem("sistemaModoExibicaoInicio", String(inicioModo));
                }

                const indiceTela = Math.floor((agora() - inicioModo) / TROCA_TELA_MS) % TELAS.length;
                navegar(TELAS[indiceTela]);
            };

            ["click", "keydown", "touchstart", "mousemove"].forEach((evento) => {
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
