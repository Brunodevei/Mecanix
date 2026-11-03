document.addEventListener("DOMContentLoaded", () => {
    const cpfInput = document.querySelector("#cpf");
    const telefoneInput = document.querySelector("#telefone");
    const placaInput = document.querySelector("#placa");
    const valorInput = document.querySelector("#valor");
    const custoTotalInput = document.querySelector("#custo_total");
    const precoFinalInput = document.querySelector("#preco_final");

    if (cpfInput) {
        cpfInput.addEventListener("input", () => {
            let valor = cpfInput.value.replace(/\D/g, "").slice(0, 11);
            if (valor.length > 9) {
                valor = valor.replace(/(\d{3})(\d{3})(\d{3})(\d{1,2})/, "$1.$2.$3-$4");
            } else if (valor.length > 6) {
                valor = valor.replace(/(\d{3})(\d{3})(\d{1,3})/, "$1.$2.$3");
            } else if (valor.length > 3) {
                valor = valor.replace(/(\d{3})(\d{1,3})/, "$1.$2");
            }
            cpfInput.value = valor;
        });
    }

    if (telefoneInput) {
        telefoneInput.addEventListener("input", () => {
            let valor = telefoneInput.value.replace(/\D/g, "").slice(0, 11);
            if (valor.length > 10) {
                valor = valor.replace(/(\d{2})(\d{5})(\d{4})/, "($1) $2-$3");
            } else if (valor.length > 6) {
                valor = valor.replace(/(\d{2})(\d{4})(\d{1,4})/, "($1) $2-$3");
            } else if (valor.length > 2) {
                valor = valor.replace(/(\d{2})(\d{1,5})/, "($1) $2");
            } else if (valor.length > 0) {
                valor = valor.replace(/(\d{1,2})/, "($1");
            }
            telefoneInput.value = valor;
        });
    }

    if (placaInput) {
        placaInput.addEventListener("input", () => {
            placaInput.value = placaInput.value
                .toUpperCase()
                .replace(/[^A-Z0-9]/g, "")
                .slice(0, 7);
        });
    }

    const formatarMoeda = (input) => {
        if (!input) return;
        input.addEventListener("input", () => {
            let valor = input.value
                .replace(/\./g, ",")
                .replace(/[^\d,]/g, "");
            const partes = valor.split(",");
            if (partes.length > 2) {
                valor = partes[0] + "," + partes.slice(1).join("");
            }
            if (partes[1]) {
                valor = partes[0] + "," + partes[1].slice(0, 2);
            }
            input.value = valor;
        });
    };

    formatarMoeda(valorInput);
    formatarMoeda(custoTotalInput);
    formatarMoeda(precoFinalInput);

    let idOrdemParaExcluir = null;

    function abrirModalExclusao(idOrdem) {
        idOrdemParaExcluir = idOrdem;
        const modal = document.getElementById('modal-exclusao');
        if (modal) {
            modal.style.display = 'flex';
        }
    }

    function fecharModalExclusao() {
        idOrdemParaExcluir = null;
        const modal = document.getElementById('modal-exclusao');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    function fecharToast() {
        const toast = document.getElementById('toast-message');
        if (toast) {
            toast.classList.add('hide');
            setTimeout(() => {
                toast.remove();
            }, 400);
        }
    }

    const toast = document.getElementById('toast-message');
    if (toast) {
        setTimeout(() => {
            fecharToast();
        }, 4000);
    }

    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('btn-excluir-ordem')) {
            const idOrdem = e.target.getAttribute('data-id');
            abrirModalExclusao(idOrdem);
        }
    });

    const btnCancelar = document.getElementById('btn-cancelar-exclusao');
    if (btnCancelar) {
        btnCancelar.addEventListener('click', () => {
            fecharModalExclusao();
        });
    }

    const btnConfirmar = document.getElementById('btn-confirmar-exclusao');
    if (btnConfirmar) {
        btnConfirmar.addEventListener('click', () => {
            if (idOrdemParaExcluir) {
                const form = document.getElementById(`form-excluir-${idOrdemParaExcluir}`);
                if (form) {
                    form.submit();
                }
            }
        });
    }
});