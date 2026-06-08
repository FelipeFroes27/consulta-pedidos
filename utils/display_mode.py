import streamlit.components.v1 as components


def ativar_modo_exibicao():
    components.html(
        """
        <script>
        (() => {
            const INATIVIDADE_MS = 5 * 60 * 1000;
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
                removerTransicao();
            };

            const criarTransicao = () => {
                if (parentDocument.getElementById("display-mode-transition")) {
                    return;
                }

                const estilo = parentDocument.createElement("style");
                estilo.id = "display-mode-transition-style";
                estilo.innerHTML = `
                    #display-mode-transition {
                        position: fixed;
                        inset: 0;
                        z-index: 9999999;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        background: rgba(255, 255, 255, 0.94);
                        color: #000000;
                        font: 800 20px Arial, sans-serif;
                        opacity: 0;
                        pointer-events: none;
                        transition: opacity .45s ease;
                    }
                    #display-mode-transition.active {
                        opacity: 1;
                    }
                `;

                const overlay = parentDocument.createElement("div");
                overlay.id = "display-mode-transition";
                overlay.textContent = "Modo de exibicao";

                parentDocument.head.appendChild(estilo);
                parentDocument.body.appendChild(overlay);
            };

            const mostrarTransicao = () => {
                criarTransicao();
                const overlay = parentDocument.getElementById("display-mode-transition");
                requestAnimationFrame(() => overlay.classList.add("active"));
            };

            function removerTransicao() {
                const overlay = parentDocument.getElementById("display-mode-transition");
                const estilo = parentDocument.getElementById("display-mode-transition-style");
                if (overlay) overlay.remove();
                if (estilo) estilo.remove();
            }

            const navegar = (destino) => {
                if (caminhoAtual() === destino) {
                    return;
                }

                mostrarTransicao();
                setTimeout(() => {
                    parentWindow.location.href = destino;
                }, 550);
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
