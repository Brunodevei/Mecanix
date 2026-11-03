document.addEventListener("DOMContentLoaded", () => {
    const cpfInput = document.querySelector("#cpf");
    const telefoneInput = document.querySelector("#telefone");
    const placaInput = document.querySelector("#placa");
    const valorInput = document.querySelector("#valor");

    if (cpfInput) {
        cpfInput.addEventListener("input", () => {
            let valor = cpfInput.value.replace(/\D/g, "").slice(0, 11);

            if (valor.length > 9) {
                valor = valor.replace(
                    /(\d{3})(\d{3})(\d{3})(\d{1,2})/,
                    "$1.$2.$3-$4"
                );
            } else if (valor.length > 6) {
                valor = valor.replace(
                    /(\d{3})(\d{3})(\d{1,3})/,
                    "$1.$2.$3"
                );
            } else if (valor.length > 3) {
                valor = valor.replace(
                    /(\d{3})(\d{1,3})/,
                    "$1.$2"
                );
            }

            cpfInput.value = valor;
        });
    }

    if (telefoneInput) {
        telefoneInput.addEventListener("input", () => {
            let valor = telefoneInput.value.replace(/\D/g, "").slice(0, 11);

            if (valor.length > 10) {
                valor = valor.replace(
                    /(\d{2})(\d{5})(\d{4})/,
                    "($1) $2-$3"
                );
            } else if (valor.length > 6) {
                valor = valor.replace(
                    /(\d{2})(\d{4})(\d{1,4})/,
                    "($1) $2-$3"
                );
            } else if (valor.length > 2) {
                valor = valor.replace(
                    /(\d{2})(\d{1,5})/,
                    "($1) $2"
                );
            } else if (valor.length > 0) {
                valor = valor.replace(
                    /(\d{1,2})/,
                    "($1"
                );
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

    if (valorInput) {
        valorInput.addEventListener("input", () => {
            let valor = valorInput.value
                .replace(/\./g, ",")
                .replace(/[^\d,]/g, "");

            const partes = valor.split(",");

            if (partes.length > 2) {
                valor = partes[0] + "," + partes.slice(1).join("");
            }

            if (partes[1]) {
                valor = partes[0] + "," + partes[1].slice(0, 2);
            }

            valorInput.value = valor;
        });
    }
});