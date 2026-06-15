package com.microservice.reportes.client;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.http.MediaType;

import java.util.List;

/**
 * Cliente para llamar al microservicio mascota-matcher (FastAPI, puerto 8000).
 * Úsalo desde ReportesServiceImpl o desde un endpoint dedicado de comparación.
 */
@Service
public class MascotaMatchClient {

    private final WebClient webClient;

    public MascotaMatchClient(
            WebClient.Builder webClientBuilder,
            @Value("${matcher.service.url:http://localhost:8000}") String matcherUrl) {
        this.webClient = webClientBuilder.baseUrl(matcherUrl).build();
    }

    // ────────────────────────────────────────────────
    // DTOs internos (reflejo de models/mascota.py)
    // ────────────────────────────────────────────────

    public record MascotaDTO(
            Long id,
            String nombre,
            String raza,
            Integer edad,
            String descripcion,
            Long usuarioId,
            String especie,   // "PERRO" | "GATO" | "HURON" | "ROEDOR" | "OTRO"
            String estado     // "PERDIDO" | "ENCONTRADO"
    ) {}

    public record MatchRequest(
            MascotaDTO mascota_perdida,
            List<MascotaDTO> candidatas
    ) {}

    public record MatchResult(
            Long mascota_id,
            double score,
            Object detalle,
            boolean alerta
    ) {}

    // ────────────────────────────────────────────────
    // Llamada al endpoint POST /api/match
    // ────────────────────────────────────────────────

    /**
     * Envía una mascota perdida y la lista de candidatas al motor de coincidencias.
     * Retorna los resultados ordenados por score descendente.
     *
     * Ejemplo de uso desde ReportesServiceImpl:
     *   List<MascotaMatchClient.MatchResult> matches =
     *       matchClient.buscarCoincidencias(mascotaPerdida, candidatas);
     *   matches.stream()
     *          .filter(MatchResult::alerta)
     *          .forEach(r -> notificarUsuario(r.mascota_id()));
     */
    public List<MatchResult> buscarCoincidencias(MascotaDTO perdida, List<MascotaDTO> candidatas) {
        MatchRequest request = new MatchRequest(perdida, candidatas);

        return webClient.post()
                .uri("/api/match")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(request)
                .retrieve()
                .bodyToFlux(MatchResult.class)
                .collectList()
                .block();
    }

    /** Verifica que el servicio matcher esté activo. */
    public boolean isHealthy() {
        try {
            var response = webClient.get()
                    .uri("/api/health")
                    .retrieve()
                    .bodyToMono(String.class)
                    .block();
            return response != null && response.contains("ok");
        } catch (Exception e) {
            return false;
        }
    }
}
