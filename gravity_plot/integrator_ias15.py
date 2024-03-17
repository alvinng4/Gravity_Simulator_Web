import numpy as np
import rich.progress

from common import acceleration

class IAS15:
    def __init__(self, simulator, objects_count, x, v, m, G, tf, tolerance, is_c_lib):
        self.progress_bar = rich.progress.Progress(
            rich.progress.BarColumn(),
            rich.progress.TextColumn("[green]{task.percentage:>3.0f}%"),
            rich.progress.TextColumn("•"),
            rich.progress.TimeElapsedColumn(),
            rich.progress.TextColumn("•"),
            rich.progress.TimeRemainingColumn(),
        )
        if is_c_lib == True:
            self.c_lib = simulator.c_lib 
            pass
        elif is_c_lib == False:
            self.sol_state, self.sol_time, self.sol_dt = self.simulation_numpy(
                objects_count,
                x,
                v,
                m,
                G,
                tf,
                tolerance,
            )

    def simulation_c_lib(self, objects_count, x, v, m, G, tf, tolerance):
        pass

    def simulation_numpy(self, objects_count, x, v, m, G, tf, tolerance):
        # Recommended tolerance: 1e-9

        # Safety factors for step-size control
        safety_fac = 0.25

        # For fixed step integration, choose exponent = 0
        exponent = 1.0 / 7.0

        # Allocate for dense output:
        npts = 50000
        sol_state = np.zeros((npts, objects_count * 2 * 3))
        sol_time = np.zeros(npts)
        sol_dt = np.zeros(npts)

        # Initial values
        sol_state[0] = np.concatenate(
            (np.reshape(x, objects_count * 3), np.reshape(v, objects_count * 3))
        )
        t = 0.0
        sol_time[0] = 0.0
        sol_dt[0] = 0.0

        # Tolerance of predictor-corrector algorithm
        tolerance_pc = 1e-16

        # Initializing auxiliary variables
        nodes, dim_nodes = self.ias15_radau_spacing()
        aux_c = self.ias15_aux_c()    
        aux_r = self.ias15_aux_r()

        aux_b0 = np.zeros((dim_nodes - 1, objects_count, 3))
        aux_b = np.zeros((dim_nodes - 1, objects_count, 3))
        aux_g = np.zeros((dim_nodes - 1, objects_count, 3))
        aux_e = np.zeros((dim_nodes - 1, objects_count, 3))

        a = acceleration(objects_count, x, m, G)

        dt = self.ias15_initial_time_step(objects_count, 15, x, v, a, m, G)

        ias15_refine_flag = 0
        count = 0
        with self.progress_bar as progress_bar:
            task = progress_bar.add_task("", total=tf)
            while True:
                (
                    x,
                    v,
                    a,
                    t,
                    dt,
                    aux_g,
                    aux_b,
                    aux_e,
                    aux_b0,
                    ias15_integrate_flag,
                    ias15_refine_flag,
                ) = self.ias15_step(
                    objects_count,
                    x,
                    v,
                    a,
                    t,
                    dt,
                    tf,
                    dim_nodes,
                    nodes,
                    aux_b0,
                    aux_b,
                    aux_c,
                    aux_e,
                    aux_g,
                    aux_r,
                    tolerance,
                    tolerance_pc,
                    exponent,
                    safety_fac,
                    ias15_refine_flag,
                    m,
                    G,
                )

                # Update step
                progress_bar.update(task, completed=t)
                count += 1

                # Store step
                sol_state[count] = np.concatenate(
                    (np.reshape(x, objects_count * 3), np.reshape(v, objects_count * 3))
                )
                sol_time[count] = t
                sol_dt[count] = dt

                # Detect end of integration
                if ias15_integrate_flag == 2:
                    progress_bar.stop()
                    break

                # Check buffer size and extend if needed :
                if (count + 1) == len(sol_state):
                    sol_state = np.concatenate(
                        (sol_state, np.zeros((npts, objects_count * 2 * 3)))
                    )
                    sol_time = np.concatenate((sol_time, np.zeros(npts)))
                    sol_dt = np.concatenate((sol_dt, np.zeros(npts)))

            return (
                sol_state[0 : count + 1],
                sol_time[0 : count + 1],
                sol_dt[0 : count + 1],
            )


    def ias15_step(
        self,
        objects_count,
        x0,
        v0,
        a0,
        t,
        dt,
        tf,
        dim_nodes,
        nodes,
        aux_b0,
        aux_b,
        aux_c,
        aux_e,
        aux_g,
        aux_r,
        tolerance,
        tolerance_pc,
        exponent,
        safety_fac,
        ias15_refine_flag,
        m,
        G,
    ):
        """
        Advance IAS15 for one step
        """
        # Main Loop
        ias15_integrate_flag = 0
        while True:
            # Loop for predictor-corrector algorithm
            # 12 = max iterations
            for _ in range(12):
                aux_a = np.zeros((dim_nodes, objects_count, 3))

                # Advance along the Gauss-Radau sequence
                for i in range(dim_nodes):
                    # Estimate position and velocity with current aux_b and nodes
                    x = self.ias15_approx_pos(x0, v0, a0, nodes[i], aux_b, dt)
                    v = self.ias15_approx_vel(v0, a0, nodes[i], aux_b, dt)

                    # Evaluate force function and store result
                    aux_a[i] = acceleration(objects_count, x, m, G)
                    aux_g = self.ias15_compute_aux_g(aux_g, aux_r, aux_a, i)
                    aux_b = self.ias15_compute_aux_b(aux_b, aux_g, aux_c, i)

                # Estimate convergence
                delta_b7 = aux_b[-1] - aux_b0[-1]
                if np.max(np.abs(delta_b7)) / np.max(np.abs(aux_a[-1])) < tolerance_pc:
                    break
                aux_b0 = aux_b

            # Advance step
            x = self.ias15_approx_pos(x0, v0, a0, 1.0, aux_b, dt)
            v = self.ias15_approx_vel(v0, a0, 1.0, aux_b, dt)
            a = acceleration(objects_count, x, m, G)

            # Estimate relative error
            error_b7 = np.max(np.abs(aux_b[-1])) / np.max(np.abs(a))
            error = (error_b7 / tolerance) ** exponent

            # Step-size for the next step
            dt_new = dt / error

            # Accept the step
            if error <= 1:
                # Report accepted step
                ias15_integrate_flag = 1
                t += dt
                aux_b0 = aux_b
                aux_b, aux_e = self.ias15_refine_aux_b(
                    aux_b, aux_e, dt, dt_new, ias15_refine_flag
                )
                ias15_refine_flag = 1

                if t >= tf:
                    ias15_integrate_flag = 2
                    break

            # Step size for the next iteration
            if (dt_new / dt) > (1.0 / safety_fac):
                dt = dt / safety_fac
            elif dt_new < 1e-12:
                dt = dt * safety_fac
            else:
                dt = dt_new

            # Correct overshooting
            if t + dt > tf:
                dt = tf - t

            if ias15_integrate_flag > 0:
                break

        return (
            x,
            v,
            a,
            t,
            dt,
            aux_g,
            aux_b,
            aux_e,
            aux_b0,
            ias15_integrate_flag,
            ias15_refine_flag,
        )

    @staticmethod
    def ias15_approx_pos(x0, v0, a0, node, aux_b, dt):
        x = x0 + dt * node * (
            v0
            + dt
            * node
            * (
                a0
                + node
                * (
                    aux_b[0] / 3.0
                    + node
                    * (
                        aux_b[1] / 6.0
                        + node
                        * (
                            aux_b[2] / 10.0
                            + node
                            * (
                                aux_b[3] / 15.0
                                + node
                                * (
                                    aux_b[4] / 21.0
                                    + node * (aux_b[5] / 28.0 + node * aux_b[6] / 36.0)
                                )
                            )
                        )
                    )
                )
            )
            / 2.0
        )

        return x

    @staticmethod
    def ias15_approx_vel(v0, a0, node, aux_b, dt):
        v = v0 + dt * node * (
            a0
            + node
            * (
                aux_b[0] / 2.0
                + node
                * (
                    aux_b[1] / 3.0
                    + node
                    * (
                        aux_b[2] / 4.0
                        + node
                        * (
                            aux_b[3] / 5.0
                            + node
                            * (
                                aux_b[4] / 6.0
                                + node * (aux_b[5] / 7.0 + node * aux_b[6] / 8.0)
                            )
                        )
                    )
                )
            )
        )

        return v

    @staticmethod
    def ias15_initial_time_step(
        objects_count: int,
        power: int,
        x,
        v,
        a,
        m,
        G,
    ) -> float:
        """
        Calculate the initial time step for IAS15

        Reference: Moving Planets Around: An Introduction to N-Body Simulations Applied to Exoplanetary Systems
        Chapter 8, Page 149
        """
        d_0 = np.max(np.abs(x))
        d_1 = np.max(np.abs(a))

        if d_0 < 1e-5 or d_1 < 1e-5:
            dt_0 = 1e-6
        else:
            dt_0 = 0.01 * (d_0 / d_1)

        x_1 = x + dt_0 * v
        # v_1 = v + dt_0 * a
        a_1 = acceleration(objects_count, x_1, m, G)
        d_2 = np.max(np.abs(a_1 - a)) / dt_0

        if max(d_1, d_2) <= 1e-15:
            dt_1 = max(1e-6, dt_0 * 1e-3)
        else:
            dt_1 = (0.01 / max(d_1, d_2)) ** (1.0 / (1.0 + power))
        dt = min(100 * dt_0, dt_1)

        return dt
    
    @staticmethod
    def ias15_radau_spacing():
        """
        Return the the nodes and its dimension for IAS15

        :rtype: numpy.array, int
        """
        dim_nodes = 8
        nodes = np.zeros(dim_nodes)

        nodes[0] = 0.0
        nodes[1] = 0.056262560536922146465652191032
        nodes[2] = 0.180240691736892364987579942809
        nodes[3] = 0.352624717113169637373907770171
        nodes[4] = 0.547153626330555383001448557652
        nodes[5] = 0.734210177215410531523210608306
        nodes[6] = 0.885320946839095768090359762932
        nodes[7] = 0.977520613561287501891174500429

        return nodes, dim_nodes

    @staticmethod
    def ias15_compute_aux_b(aux_b, aux_g, aux_c, i):
        """
        Calculate the auxiliary coefficients b for IAS15

        :rtype: numpy.array
        """

        if i >= 1:
            aux_b[0] = (
                aux_c[0, 0] * aux_g[0]
                + aux_c[1, 0] * aux_g[1]
                + aux_c[2, 0] * aux_g[2]
                + aux_c[3, 0] * aux_g[3]
                + aux_c[4, 0] * aux_g[4]
                + aux_c[5, 0] * aux_g[5]
                + aux_c[6, 0] * aux_g[6]
            )
        if i >= 2:
            aux_b[1] = (
                aux_c[1, 1] * aux_g[1]
                + aux_c[2, 1] * aux_g[2]
                + aux_c[3, 1] * aux_g[3]
                + aux_c[4, 1] * aux_g[4]
                + aux_c[5, 1] * aux_g[5]
                + aux_c[6, 1] * aux_g[6]
            )
        if i >= 3:
            aux_b[2] = (
                aux_c[2, 2] * aux_g[2]
                + aux_c[3, 2] * aux_g[3]
                + aux_c[4, 2] * aux_g[4]
                + aux_c[5, 2] * aux_g[5]
                + aux_c[6, 2] * aux_g[6]
            )
        if i >= 4:
            aux_b[3] = (
                aux_c[3, 3] * aux_g[3]
                + aux_c[4, 3] * aux_g[4]
                + aux_c[5, 3] * aux_g[5]
                + aux_c[6, 3] * aux_g[6]
            )
        if i >= 5:
            aux_b[4] = (
                aux_c[4, 4] * aux_g[4] + aux_c[5, 4] * aux_g[5] + aux_c[6, 4] * aux_g[6]
            )
        if i >= 6:
            aux_b[5] = aux_c[5, 5] * aux_g[5] + aux_c[6, 5] * aux_g[6]
        if i >= 7:
            aux_b[6] = aux_c[6, 6] * aux_g[6]

        return aux_b

    @staticmethod
    def ias15_aux_c():
        """
        Return the auxiliary coefficients c for IAS15

        :rtype: numpy.array
        :rshape: (8, 8)
        """
        aux_c = np.zeros((8, 8))
        for i in range(8):
            aux_c[i, i] = 1.0

        aux_c[1, 0] = -0.0562625605369221464656522

        aux_c[2, 0] = 0.01014080283006362998648180399549641417413495311078
        aux_c[2, 1] = -0.2365032522738145114532321

        aux_c[3, 0] = -0.0035758977292516175949344589284567187362040464593728
        aux_c[3, 1] = 0.09353769525946206589574845561035371499343547051116
        aux_c[3, 2] = -0.5891279693869841488271399

        aux_c[4, 0] = 0.0019565654099472210769005672379668610648179838140913
        aux_c[4, 1] = -0.054755386889068686440808430671055022602028382584495
        aux_c[4, 2] = 0.41588120008230686168862193041156933067050816537030
        aux_c[4, 3] = -1.1362815957175395318285885

        aux_c[5, 0] = -0.0014365302363708915424459554194153247134438571962198
        aux_c[5, 1] = 0.042158527721268707707297347813203202980228135395858
        aux_c[5, 2] = -0.36009959650205681228976647408968845289781580280782
        aux_c[5, 3] = 1.2501507118406910258505441186857527694077565516084
        aux_c[5, 4] = -1.8704917729329500633517991

        aux_c[6, 0] = 0.0012717903090268677492943117622964220889484666147501
        aux_c[6, 1] = -0.038760357915906770369904626849901899108502158354383
        aux_c[6, 2] = 0.36096224345284598322533983078129066420907893718190
        aux_c[6, 3] = -1.4668842084004269643701553461378480148761655599754
        aux_c[6, 4] = 2.9061362593084293014237914371173946705384212479246
        aux_c[6, 5] = -2.7558127197720458314421589

        aux_c[7, 0] = -0.0012432012432012432012432013849038719237133940238163
        aux_c[7, 1] = 0.039160839160839160839160841227582657239289159887563
        aux_c[7, 2] = -0.39160839160839160839160841545895262429018228668896
        aux_c[7, 3] = 1.7948717948717948717948719027866738711862551337629
        aux_c[7, 4] = -4.3076923076923076923076925231853900723503338586335
        aux_c[7, 5] = 5.6000000000000000000000001961129300233768803845526
        aux_c[7, 6] = -3.7333333333333333333333334

        return aux_c

    @staticmethod
    def ias15_compute_aux_g(aux_g, aux_r, aux_a, i):
        # Retrieve required accelerations:
        F1 = aux_a[0]
        F2 = aux_a[1]
        F3 = aux_a[2]
        F4 = aux_a[3]
        F5 = aux_a[4]
        F6 = aux_a[5]
        F7 = aux_a[6]
        F8 = aux_a[7]

        # Update aux_g using the accelerations:
        if i >= 1:
            aux_g[0] = (F2 - F1) * aux_r[1, 0]
        if i >= 2:
            aux_g[1] = ((F3 - F1) * aux_r[2, 0] - aux_g[0]) * aux_r[2, 1]
        if i >= 3:
            aux_g[2] = (
                ((F4 - F1) * aux_r[3, 0] - aux_g[0]) * aux_r[3, 1] - aux_g[1]
            ) * aux_r[3, 2]
        if i >= 4:
            aux_g[3] = (
                (((F5 - F1) * aux_r[4, 0] - aux_g[0]) * aux_r[4, 1] - aux_g[1])
                * aux_r[4, 2]
                - aux_g[2]
            ) * aux_r[4, 3]
        if i >= 5:
            aux_g[4] = (
                (
                    (((F6 - F1) * aux_r[5, 0] - aux_g[0]) * aux_r[5, 1] - aux_g[1])
                    * aux_r[5, 2]
                    - aux_g[2]
                )
                * aux_r[5, 3]
                - aux_g[3]
            ) * aux_r[5, 4]
        if i >= 6:
            aux_g[5] = (
                (
                    (
                        (((F7 - F1) * aux_r[6, 0] - aux_g[0]) * aux_r[6, 1] - aux_g[1])
                        * aux_r[6, 2]
                        - aux_g[2]
                    )
                    * aux_r[6, 3]
                    - aux_g[3]
                )
                * aux_r[6, 4]
                - aux_g[4]
            ) * aux_r[6, 5]
        if i >= 7:
            aux_g[6] = (
                (
                    (
                        (
                            (((F8 - F1) * aux_r[7, 0] - aux_g[0]) * aux_r[7, 1] - aux_g[1])
                            * aux_r[7, 2]
                            - aux_g[2]
                        )
                        * aux_r[7, 3]
                        - aux_g[3]
                    )
                    * aux_r[7, 4]
                    - aux_g[4]
                )
                * aux_r[7, 5]
                - aux_g[5]
            ) * aux_r[7, 6]

        return aux_g

    @staticmethod
    def ias15_aux_r():
        """
        Return the auxiliary coefficients r for IAS15

        :rtype: numpy.array
        :rshape: (8, 8)
        """
        aux_r = np.zeros((8, 8))

        aux_r[1, 0] = 17.773808914078000840752659565672904106978971632681
        aux_r[2, 0] = 5.5481367185372165056928216140765061758579336941398
        aux_r[3, 0] = 2.8358760786444386782520104428042437400879003147949
        aux_r[4, 0] = 1.8276402675175978297946077587371204385651628457154
        aux_r[5, 0] = 1.3620078160624694969370006292445650994197371928318
        aux_r[6, 0] = 1.1295338753367899027322861542728593509768148769105
        aux_r[7, 0] = 1.0229963298234867458386119071939636779024159134103

        aux_r[2, 1] = 8.0659386483818866885371256689687154412267416180207
        aux_r[3, 1] = 3.3742499769626352599420358188267460448330087696743
        aux_r[4, 1] = 2.0371118353585847827949159161566554921841792590404
        aux_r[5, 1] = 1.4750402175604115479218482480167404024740127431358
        aux_r[6, 1] = 1.2061876660584456166252036299646227791474203527801
        aux_r[7, 1] = 1.0854721939386423840467243172568913862030118679827

        aux_r[3, 2] = 5.8010015592640614823286778893918880155743979164251
        aux_r[4, 2] = 2.7254422118082262837742722003491334729711450288807
        aux_r[5, 2] = 1.8051535801402512604391147435448679586574414080693
        aux_r[6, 2] = 1.4182782637347391537713783674858328433713640692518
        aux_r[7, 2] = 1.2542646222818777659905422465868249586862369725826

        aux_r[4, 3] = 5.1406241058109342286363199091504437929335189668304
        aux_r[5, 3] = 2.6206449263870350811541816031933074696730227729812
        aux_r[6, 3] = 1.8772424961868100972169920283109658335427446084411
        aux_r[7, 3] = 1.6002665494908162609916716949161150366323259154408

        aux_r[5, 4] = 5.3459768998711075141214909632277898045770336660354
        aux_r[6, 4] = 2.9571160172904557478071040204245556508352776929762
        aux_r[7, 4] = 2.3235983002196942228325345451091668073608955835034

        aux_r[6, 5] = 6.6176620137024244874471284891193925737033291491748
        aux_r[7, 5] = 4.1099757783445590862385761824068782144723082633980

        aux_r[7, 6] = 10.846026190236844684706431007823415424143683137181

        return aux_r

    @staticmethod
    def ias15_refine_aux_b(aux_b, aux_e, dt, dt_new, ias15_refine_flag):
        if ias15_refine_flag != 0:
            delta_aux_b = aux_b - aux_e
        else:
            delta_aux_b = aux_b * 0

        # Compute q and the powers of q:
        q = dt_new / dt
        q2 = q * q
        q3 = q2 * q
        q4 = q3 * q
        q5 = q4 * q
        q6 = q5 * q
        q7 = q6 * q

        aux_e[0] = q * (
            aux_b[6] * 7.0
            + aux_b[5] * 6.0
            + aux_b[4] * 5.0
            + aux_b[3] * 4.0
            + aux_b[2] * 3.0
            + aux_b[1] * 2.0
            + aux_b[0]
        )
        aux_e[1] = q2 * (
            aux_b[6] * 21.0
            + aux_b[5] * 15.0
            + aux_b[4] * 10.0
            + aux_b[3] * 6.0
            + aux_b[2] * 3.0
            + aux_b[1]
        )
        aux_e[2] = q3 * (
            aux_b[6] * 35.0 + aux_b[5] * 20.0 + aux_b[4] * 10.0 + aux_b[3] * 4.0 + aux_b[2]
        )
        aux_e[3] = q4 * (aux_b[6] * 35.0 + aux_b[5] * 15.0 + aux_b[4] * 5.0 + aux_b[3])
        aux_e[4] = q5 * (aux_b[6] * 21.0 + aux_b[5] * 6.0 + aux_b[4])
        aux_e[5] = q6 * (aux_b[6] * 7.0 + aux_b[5])
        aux_e[6] = q7 * aux_b[6]

        aux_b = aux_e + delta_aux_b

        return aux_b, aux_e
