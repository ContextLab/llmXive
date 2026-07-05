import numpy as np
from scipy.optimize import brentq
from typing import Tuple, Optional

def yukawa_potential(r: np.ndarray, alpha: float, mass: float) -> np.ndarray:
    """
    Calculate the Yukawa potential V(r) = -alpha * exp(-mass * r) / r.
    
    Parameters:
    -----------
    r : np.ndarray
        Array of radial distances.
    alpha : float
        Coupling strength (dimensionless).
    mass : float
        Mediator mass (inverse length units).
        
    Returns:
    --------
    np.ndarray
        Potential values at each r.
    """
    # Avoid division by zero at r=0
    r_safe = np.where(r == 0, 1e-12, r)
    return -alpha * np.exp(-mass * r_safe) / r_safe

def numerov_schrodinger(
    r: np.ndarray, 
    E: float, 
    alpha: float, 
    mass: float, 
    mu: float
) -> np.ndarray:
    """
    Solve the radial Schrödinger equation for a Yukawa potential using the Numerov method.
    
    Equation: u''(r) = 2*mu * (V(r) - E) * u(r)
    where V(r) is the Yukawa potential.
    
    Parameters:
    -----------
    r : np.ndarray
        Radial grid points (must be equally spaced).
    E : float
        Energy eigenvalue.
    alpha : float
        Coupling strength.
    mass : float
        Mediator mass.
    mu : float
        Reduced mass of the system.
        
    Returns:
    --------
    np.ndarray
        Wavefunction u(r) on the grid.
    """
    h = r[1] - r[0]
    N = len(r)
    
    # Calculate k^2(r) = 2*mu * (E - V(r))
    # Note: Numerov usually written as u'' = -k^2 u, so k^2 = 2*mu*(E-V)
    V = yukawa_potential(r, alpha, mass)
    k2 = 2 * mu * (E - V)
    
    # Numerov coefficients: g_i = 1 + h^2/12 * k2_i
    g = 1.0 + (h**2 / 12.0) * k2
    
    # Initialize wavefunction array
    u = np.zeros(N)
    
    # Boundary conditions for s-wave (l=0): u(0) = 0, u'(0) = 1 (arbitrary normalization)
    # At r=0, we start with u[0]=0, u[1]=h (approximate derivative)
    u[0] = 0.0
    u[1] = h  # Small non-zero value to start propagation
    
    # Numerov recurrence relation:
    # u_{i+1} = (2*u_i*(1 - 5*h^2*k2_i/12) - u_{i-1}*(1 + h^2*k2_{i-1}/12)) / (1 + h^2*k2_{i+1}/12)
    for i in range(1, N - 1):
        u[i+1] = (2 * u[i] * (1 - (h**2 * k2[i] / 12.0)) - 
                  u[i-1] * (1 + (h**2 * k2[i-1] / 12.0))) / g[i+1]
                  
    return u

def extract_sommerfeld_factor(
    r: np.ndarray, 
    u: np.ndarray, 
    alpha: float, 
    v: float, 
    mu: float
) -> float:
    """
    Extract the Sommerfeld enhancement factor S from the wavefunction.
    
    S = |u(r->inf) / u_free(r->inf)|^2
    For a free particle, u_free(r) ~ sin(kr + delta) ~ kr for small r.
    The enhancement is calculated by comparing the asymptotic amplitude.
    
    Parameters:
    -----------
    r : np.ndarray
        Radial grid.
    u : np.ndarray
        Numerically solved wavefunction.
    alpha : float
        Coupling strength.
    v : float
        Relative velocity.
    mu : float
        Reduced mass.
        
    Returns:
    --------
    float
        Sommerfeld enhancement factor S.
    """
    k = mu * v
    # Free wavefunction normalization: u_free ~ sin(kr) ~ kr at small r
    # We normalize u such that u(r) ~ sin(kr + delta) at large r
    # For simplicity, we compare the amplitude at the last grid point
    # assuming the potential is negligible there.
    
    # Asymptotic behavior: u(r) ~ A * sin(kr + delta)
    # We estimate A by fitting or by taking the envelope at large r
    # Simple approximation: S = (|u(r_max)| / (k * r_max))^2 * (normalization factor)
    # A more robust way: compare to the Coulomb limit or free case at the same r
    
    # Free case at r_max: u_free(r_max) = sin(k * r_max) / k (normalized to unit flux)
    # But for enhancement, we look at the ratio of probability densities at origin
    # or the amplification of the wavefunction at large r compared to free case.
    
    # Standard definition: S = |psi(0)|^2 / |psi_free(0)|^2
    # Since u(r) = r * psi(r), and u(0)=0, we look at u'(0).
    # Numerov gives u[1] ~ h * u'(0).
    # For free particle, u_free(r) = sin(kr)/k, u_free'(0) = 1.
    # So S = (u'(0) / u_free'(0))^2 = (u[1]/h)^2 / 1^2 = (u[1]/h)^2
    # However, this is only strictly true for s-wave at zero energy.
    # For finite energy, we normalize the wavefunction to unit flux at infinity.
    
    # Robust method: Normalize u to have amplitude 1 at infinity (sinusoidal envelope)
    # and compare the amplitude at r=0 (or derivative).
    # Alternatively, use the ratio of the wavefunction at the last point to the free case.
    
    # Let's use the standard approximation for the enhancement factor:
    # S = | (u(r_max) / sin(k*r_max)) * (k*r_max) / u_free_norm |^2
    # This is complex. A simpler, standard Numerov approach for S-factor:
    # Integrate from 0 to r_max, normalize to unit flux at r_max, then check u'(0).
    
    # Practical implementation:
    # 1. Solve with u[0]=0, u[1]=h.
    # 2. At r_max, the solution behaves as A*sin(k*r_max + delta).
    # 3. The free solution (alpha=0) with same BCs behaves as sin(k*r_max)/k * k = sin(k*r_max).
    # 4. Actually, let's just compute the ratio of the wavefunction squared at a large r
    #    relative to the free case, normalized by the phase space.
    
    # Simplified robust calculation:
    # Normalize the calculated u to have amplitude 1 at large r (approximate envelope)
    # Then S = (u'(0) / k)^2 where u'(0) is the slope at origin for the normalized wave.
    
    # Since u[1] = h * u'(0), and for free particle u_free(r) ~ sin(kr), u_free'(0)=k.
    # So S = (u'[0]_calc / k)^2.
    # But we need to normalize the amplitude.
    
    # Let's normalize u such that at large r, it matches sin(kr) amplitude.
    # Find the last few points, estimate amplitude A.
    # u(r) ~ A * sin(kr + phi).
    # We can estimate A by max(u[-10:]) or similar.
    # Then normalized u' at 0 is (u[1]/h) * (1/A).
    # Free case A_free = 1/k (if we set u_free = sin(kr)/k).
    # This is getting messy. Let's use the standard formula:
    # S = | (u(r) / r) / (sin(kr)/r) |^2 at r->0 ? No.
    
    # Correct standard method for Numerov:
    # 1. Solve with u(0)=0, u'(0)=1.
    # 2. At r_max, u(r_max) = A * sin(k*r_max + delta).
    # 3. The free solution with u(0)=0, u'(0)=1 is u_free(r) = sin(kr)/k.
    #    At r_max, u_free(r_max) = sin(k*r_max)/k.
    # 4. The ratio of amplitudes A / (1/k) = A*k.
    # 5. S = (A*k)^2.
    # Wait, if u'(0)=1 for both, then S = |u(r_max)/u_free(r_max)|^2? No.
    
    # Let's use the definition: S = |psi(0)|^2 / |psi_free(0)|^2.
    # psi(r) = u(r)/r. u(r) ~ r * psi(0) near 0.
    # So u'(0) = psi(0).
    # If we solve with u'(0)=1, then psi(0)=1.
    # For free particle, u_free(r) = sin(kr)/k. u_free'(0) = 1.
    # So if we solve with u'(0)=1, the ratio of psi(0) is 1? That implies S=1?
    # No, the boundary condition at infinity changes the normalization.
    
    # Correct approach:
    # Solve with u(0)=0, u'(0)=1.
    # At r_max, u(r_max) = C * sin(k*r_max + delta).
    # The free solution with u(0)=0, u'(0)=1 is u_free(r) = sin(kr)/k.
    # At r_max, u_free(r_max) = sin(k*r_max)/k.
    # The physical wavefunction is normalized to unit flux at infinity.
    # The flux is proportional to k * |C|^2.
    # For free particle, C_free = 1/k. Flux = k * (1/k)^2 = 1/k.
    # For interacting, C = u(r_max) / sin(k*r_max + delta).
    # We don't know delta.
    # Instead, we compare the derivative at the origin for the same flux.
    # S = |u'(0)|^2_interacting / |u'(0)|^2_free (for same flux).
    # If we fix flux to 1, then |u'(0)|_free = k.
    # |u'(0)|_interacting = k * S^0.5.
    # So S = (|u'(0)|_interacting / k)^2.
    # But we solved with u'(0)=1.
    # So we need to scale the solution such that the flux at infinity is 1.
    # Flux ~ k * |Amplitude|^2.
    # Our solution u has amplitude C at infinity.
    # We need to scale u by factor F such that k * |C*F|^2 = 1 => F = 1/(k*C).
    # Then u_scaled'(0) = u'(0) * F = 1 * F = 1/(k*C).
    # S = |u_scaled'(0) / k|^2? No.
    # S = |psi(0)|^2_interacting / |psi_free(0)|^2_free (for same flux).
    # psi(0) = u'(0).
    # For free, psi_free(0) = k (if flux=1).
    # For interacting, psi(0) = u_scaled'(0).
    # S = (u_scaled'(0) / k)^2 = (1/(k*C) / k)^2 = 1/(k^4 * C^2).
    # This seems off.
    
    # Let's use the simplest robust method found in literature for Numerov:
    # S = | (u(r_max) / sin(k*r_max)) * (k*r_max) |^2 ? No.
    
    # Re-evaluate:
    # u(r) ~ A sin(kr + delta) at large r.
    # Free: u_free(r) ~ (1/k) sin(kr) (if u'(0)=1).
    # We want S = |u'(0) / k|^2 where u'(0) is for the normalized wave (flux=1).
    # If we solve with u'(0)=1, then u(r) = A sin(kr+delta).
    # The free solution with u'(0)=1 is u_free = (1/k) sin(kr).
    # The ratio of amplitudes at infinity: A / (1/k) = Ak.
    # The ratio of derivatives at origin is 1/1 = 1? No, the normalization is different.
    # The physical wavefunction psi = u/r.
    # Flux J = k * |A|^2.
    # We want J=1. So we scale u by 1/sqrt(J) = 1/(A*sqrt(k)).
    # Then u_scaled'(0) = 1 / (A*sqrt(k)).
    # psi(0) = u_scaled'(0).
    # Free case: A_free = 1/k. J_free = k * (1/k)^2 = 1/k.
    # Scale free by 1/sqrt(1/k) = sqrt(k).
    # u_free_scaled'(0) = 1 * sqrt(k) = sqrt(k).
    # psi_free(0) = sqrt(k).
    # S = (u_scaled'(0) / psi_free(0))^2 = (1/(A*sqrt(k)) / sqrt(k))^2 = 1/(A^2 * k^2).
    # So S = 1 / (A^2 * k^2).
    # We need to estimate A from u(r_max).
    # u(r_max) = A sin(k*r_max + delta).
    # We don't know delta.
    # But we can estimate A by taking the envelope.
    # Or, if we choose r_max such that sin(...) ~ 1?
    # Better: A = sqrt(u(r_max)^2 + (u'(r_max)/k)^2).
    # u'(r) ~ k*A*cos(kr+delta).
    # So A^2 = u^2 + (u'/k)^2.
    # We can estimate u' at r_max using finite difference.
    
    h = r[1] - r[0]
    u_prime_last = (u[-1] - u[-2]) / h
    # Estimate amplitude A
    A_sq = u[-1]**2 + (u_prime_last / k)**2
    A = np.sqrt(A_sq)
    
    if A == 0:
        return 1.0
        
    S = 1.0 / (A**2 * k**2)
    return S

def solve_yukawa_binding_energy(
    alpha: float, 
    mass: float, 
    mu: float, 
    r_max: float = 50.0, 
    n_points: int = 1000
) -> Optional[float]:
    """
    Find the binding energy (E < 0) of the Yukawa potential using the Numerov method.
    
    Uses a shooting method to find the energy where the wavefunction decays to zero at r_max.
    
    Parameters:
    -----------
    alpha : float
        Coupling strength.
    mass : float
        Mediator mass.
    mu : float
        Reduced mass.
    r_max : float
        Maximum radial distance.
    n_points : int
        Number of grid points.
        
    Returns:
    --------
    float or None
        Binding energy E (negative value), or None if no bound state found.
    """
    r = np.linspace(0, r_max, n_points)
    h = r[1] - r[0]
    
    def wavefunction_at_boundary(E):
        # Solve Numerov for energy E
        u = numerov_schrodinger(r, E, alpha, mass, mu)
        return u[-1]
    
    # Search for bound state: E must be negative and greater than min(V)
    # Min of Yukawa potential is at r ~ 1/mass?
    # V(r) = -alpha * exp(-mass*r)/r.
    # We search in range [-alpha*mu, 0].
    # Actually, the ground state energy is roughly -alpha^2 * mu / 2 for Coulomb.
    # For Yukawa, it's similar but slightly less bound.
    # Let's search from -alpha^2 * mu to -1e-6.
    
    E_min = - (alpha**2) * mu * 2.0  # Safe lower bound
    E_max = -1e-8
    
    try:
        # Check signs at boundaries
        val_min = wavefunction_at_boundary(E_min)
        val_max = wavefunction_at_boundary(E_max)
        
        # If signs are same, we might not have a bound state or need different range
        if val_min * val_max > 0:
            # Try a wider range or return None
            # Sometimes the wavefunction doesn't cross zero in the chosen range
            # We can try to scan for a zero crossing
            Es = np.linspace(E_min, E_max, 100)
            vals = [wavefunction_at_boundary(e) for e in Es]
            for i in range(len(vals)-1):
                if vals[i] * vals[i+1] < 0:
                    E_root = brentq(wavefunction_at_boundary, Es[i], Es[i+1])
                    return E_root
            return None
        
        E_root = brentq(wavefunction_at_boundary, E_min, E_max)
        return E_root
    except ValueError:
        # No root found
        return None