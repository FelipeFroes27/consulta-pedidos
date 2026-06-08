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

            const sidebarEstaAberta = () => {
                const sidebar = parentDocument.querySelector('[data-testid="stSidebar"]');
                if (!sidebar) {
                    return false;
                }

                const largura = sidebar.getBoundingClientRect().width;
                return largura > 120;
            };

            const recolherSidebar = () => {
                if (!sidebarEstaAberta()) {
                    return;
                }

                const botao = parentDocument.querySelector(
                    '[data-testid="stSidebarCollapseButton"], [data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"]'
                );

                if (botao) {
                    botao.click();
                }
            };

            const registrarAtividade = () => {
                if (storage.getItem("sistemaModoExibicaoNavegando") === "1") {
                    return;
                }

                storage.setItem("sistemaUltimoClique", String(agora()));
                storage.removeItem("sistemaModoExibicaoAtivo");
                storage.removeItem("sistemaModoExibicaoIndice");
                storage.removeItem("sistemaModoExibicaoProximaTroca");
            };

            const navegar = (destino) => {
                if (caminhoAtual() === destino) {
                    return;
                }

                storage.setItem("sistemaModoExibicaoNavegando", "1");

                const links = Array.from(parentDocument.querySelectorAll("a[href]"));
                const linkDestino = links.find((link) => {
                    const href = new URL(link.getAttribute("href"), parentWindow.location.origin);
                    return href.pathname.replace(/\\/$/, "") === destino;
                });

                if (linkDestino) {
                    linkDestino.click();
                } else {
                    parentWindow.location.assign(new URL(destino, parentWindow.location.origin).toString());
                }

                setTimeout(() => {
                    storage.removeItem("sistemaModoExibicaoNavegando");
                }, 1200);
            };

            const verificar = () => {
                let ultimoClique = Number(storage.getItem("sistemaUltimoClique") || agora());
                if (!storage.getItem("sistemaUltimoClique")) {
                    storage.setItem("sistemaUltimoClique", String(ultimoClique));
                }

                if (!Number.isFinite(ultimoClique) || ultimoClique > agora()) {
                    ultimoClique = agora();
                    storage.setItem("sistemaUltimoClique", String(ultimoClique));
                    storage.removeItem("sistemaModoExibicaoAtivo");
                    storage.removeItem("sistemaModoExibicaoIndice");
                    storage.removeItem("sistemaModoExibicaoProximaTroca");
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
                    recolherSidebar();
                    navegar(TELAS[proximoIndice]);
                    return;
                }

                let proximaTroca = Number(storage.getItem("sistemaModoExibicaoProximaTroca") || 0);
                if (!Number.isFinite(proximaTroca) || proximaTroca > agora() + TROCA_TELA_MS) {
                    proximaTroca = 0;
                }

                if (agora() < proximaTroca) {
                    return;
                }

                const indiceAtual = Number(storage.getItem("sistemaModoExibicaoIndice") || 0);
                const proximoIndice = (indiceAtual + 1) % TELAS.length;

                storage.setItem("sistemaModoExibicaoIndice", String(proximoIndice));
                storage.setItem("sistemaModoExibicaoProximaTroca", String(agora() + TROCA_TELA_MS));
                recolherSidebar();
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
